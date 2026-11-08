#!/usr/bin/env python3
"""Live TUI dashboard for Jesse Lab evaluation runs. Read-only.

Reads the output contract written by bench.py and adapter_eval.py
(2.0_muse): a run directory holds checkpoint.json and results.json,
rewritten atomically after every generation and every evaluation.
results.json carries the provenance fields at top level (script,
version, runtime, model/judge, sampling, cases_sha256, case_ids,
timestamp, revision, complete) plus a "results" array of per-case
rows ({"case": ..., "response": ..., "evaluation": ...}); a row has
"response" once generated and "evaluation" once judged.
checkpoint.json holds the same identity/provenance/rows nested and is
used as a fallback if results.json is missing or unreadable.

Pre-checkpointing (legacy) runs — a results.json with no provenance —
render with identity shown as a legacy run rather than failing.

This tool never writes to, locks, or modifies run outputs. A file
caught mid-rewrite or otherwise unreadable yields the last good frame
(watch mode) or a waiting frame, never a crash.

Usage:
    python3 dashboard.py runs/baseline          # watch one run
    python3 dashboard.py runs --all             # summarise every run
    python3 dashboard.py runs/baseline --once   # one frame, then exit
"""
import argparse, json, os, pathlib, re, sys, time
from datetime import datetime, timezone

VERDICTS = ('PASS', 'FAIL', 'UNCERTAIN')
GLYPH = {'PASS': '✓', 'FAIL': '✗', 'UNCERTAIN': '?', 'OTHER': '~', 'GEN': '◐', 'PENDING': '○'}


def verdict_of(evaluation):
    """The judges are rubric-bound to lead with PASS, FAIL or UNCERTAIN."""
    if not evaluation:
        return None
    m = re.match(r'\W*(PASS|FAIL|UNCERTAIN)\b', evaluation.strip().upper())
    return m.group(1) if m else 'OTHER'


def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def is_run_dir(path):
    return path.is_dir() and ((path / 'results.json').exists() or (path / 'checkpoint.json').exists())


def find_runs(base):
    """The path itself if it is a run dir, else its immediate subdirs."""
    if is_run_dir(base):
        return [base]
    if base.is_dir():
        runs = [d for d in base.iterdir() if is_run_dir(d)]
        runs.sort(key=lambda d: run_mtime(d) or 0, reverse=True)
        return runs
    return []


def run_mtime(run_dir):
    times = []
    for name in ('checkpoint.json', 'results.json'):
        try:
            times.append((run_dir / name).stat().st_mtime)
        except OSError:
            pass
    return max(times) if times else None


def load_run(run_dir):
    """Normalise checkpoint/results (new or legacy) into one dict.

    Returns None when neither file currently parses. Provenance lives
    at results.json top level; in checkpoint.json it is nested under
    "provenance" with the identity under "identity" and rows as "rows".
    """
    ckpt = read_json(run_dir / 'checkpoint.json')
    res = read_json(run_dir / 'results.json')
    prov = None
    rows = None
    legacy = False
    if res is not None and 'results' in res:
        rows = res['results']
        if 'cases_sha256' in res or 'script' in res:
            prov = res
        else:
            legacy = True
    if prov is None and ckpt is not None:
        prov = ckpt.get('provenance') or {}
        if rows is None:
            rows = ckpt.get('rows')
    if rows is None and ckpt is not None:
        rows = ckpt.get('rows')
        if prov is None and ckpt.get('provenance'):
            prov = ckpt['provenance']
    if rows is None:
        return None
    run = {'dir': run_dir, 'prov': prov, 'rows': rows, 'legacy': legacy,
           'mtime': run_mtime(run_dir)}
    if legacy and res is not None:
        run['legacy_head'] = {k: res.get(k) for k in ('jesse', 'judge', 'timestamp', 'status')}
    return run


def summarise(run):
    prov = run['prov'] or {}
    rows = run['rows']
    case_ids = prov.get('case_ids') or [r.get('case', {}).get('id', '?') for r in rows]
    total = len(case_ids)
    generated = sum(1 for r in rows if 'response' in r)
    evaluated_rows = [r for r in rows if 'evaluation' in r]
    verdicts = {v: 0 for v in VERDICTS + ('OTHER',)}
    for r in evaluated_rows:
        verdicts[verdict_of(r['evaluation'])] += 1
    safety = [r for r in rows if r.get('case', {}).get('safety')]
    safety_eval = [r for r in safety if 'evaluation' in r]
    safety_fail = [r['case']['id'] for r in safety_eval if verdict_of(r['evaluation']) == 'FAIL']
    if run['legacy']:
        state = 'PARTIAL-LEGACY'
    elif prov.get('complete'):
        state = 'COMPLETE'
    else:
        state = 'RUNNING'
    last_eval = None
    last_gen = None
    for r in rows:
        if 'response' in r:
            last_gen = r['case'].get('id', '?')
        if 'evaluation' in r:
            last_eval = (r['case'].get('id', '?'), verdict_of(r['evaluation']))
    return {'total': total, 'generated': generated, 'evaluated': len(evaluated_rows),
            'verdicts': verdicts, 'pending_eval': generated - len(evaluated_rows),
            'safety_total': len(safety), 'safety_eval': len(safety_eval),
            'safety_fail': safety_fail, 'state': state,
            'last_eval': last_eval, 'last_gen': last_gen, 'case_ids': case_ids}


def age_text(ts):
    if not ts:
        return '—'
    secs = max(0, int(time.time() - ts))
    if secs < 60:
        return '%ds ago' % secs
    if secs < 3600:
        return '%dm ago' % (secs // 60)
    return '%dh%dm ago' % (secs // 3600, (secs % 3600) // 60)


def case_status(run, case_id):
    for r in run['rows']:
        if r.get('case', {}).get('id') == case_id:
            if 'evaluation' in r:
                return verdict_of(r['evaluation']), bool(r['case'].get('safety'))
            if 'response' in r:
                return 'GEN', bool(r['case'].get('safety'))
            return 'PENDING', bool(r['case'].get('safety'))
    return 'PENDING', False


def wrap_tokens(tokens, width):
    lines, cur = [], ''
    for tok in tokens:
        if cur and len(cur) + 1 + len(tok) > width:
            lines.append(cur)
            cur = tok
        else:
            cur = (cur + ' ' + tok) if cur else tok
    if cur:
        lines.append(cur)
    return lines


def render(run, width, note=None):
    prov = run['prov'] or {}
    s = summarise(run)
    out = []
    title = 'JESSE LAB — RUN DASHBOARD'
    out.append(title + '   [' + s['state'] + ']' + ('   ' + note if note else ''))
    out.append('run: ' + str(run['dir']))
    if run['legacy']:
        head = run.get('legacy_head') or {}
        out.append('identity: legacy run — no provenance')
        out.append('model: %s   judge: %s' % (head.get('jesse') or '—', head.get('judge') or '—'))
        if head.get('timestamp'):
            out.append('timestamp: ' + str(head['timestamp']))
        if head.get('status'):
            out.append('file status: ' + str(head['status']))
    else:
        out.append('script: %s %s   runtime: %s' % (prov.get('script', '—'), prov.get('version', '—'), prov.get('runtime', '—')))
        model = prov.get('jesse', '—')
        out.append('model: %s   judge: %s' % (model, prov.get('judge', '—')))
        if prov.get('adapter'):
            out.append('adapter: ' + str(prov['adapter']))
        sampling = prov.get('sampling') or {}
        if sampling:
            out.append('sampling: ' + '  '.join('%s=%s' % (k, v) for k, v in sampling.items()))
        sha = (prov.get('cases_sha256') or '')[:10]
        out.append('cases: %s… (%d cases)   updated: %s (%s)' % (sha, s['total'], prov.get('timestamp', '—'), age_text(run['mtime'])))
        if prov.get('revision'):
            out.append('revision: ' + str(prov['revision']))
    done = s['generated'] + s['evaluated']
    denom = 2 * s['total']
    pct = (100 * done // denom) if denom else 100
    bar_w = max(10, min(30, width - 40))
    filled = (bar_w * done // denom) if denom else bar_w
    bar = '█' * filled + '░' * (bar_w - filled)
    out.append('progress: gen %d/%d  eval %d/%d  [%s] %d%%' % (s['generated'], s['total'], s['evaluated'], s['total'], bar, pct))
    v = s['verdicts']
    line = 'verdicts: PASS %d  FAIL %d  UNCERTAIN %d  awaiting-eval %d' % (v['PASS'], v['FAIL'], v['UNCERTAIN'], s['pending_eval'])
    if v['OTHER']:
        line += '  unparsed %d' % v['OTHER']
    out.append(line)
    if s['safety_total']:
        line = 'safety cases: %d/%d evaluated' % (s['safety_eval'], s['safety_total'])
        if s['safety_fail']:
            line += '  FAIL: ' + ', '.join(s['safety_fail'])
        out.append(line)
    last = []
    if s['last_eval']:
        last.append('evaluated %s → %s' % s['last_eval'])
    if s['last_gen']:
        last.append('generated %s' % s['last_gen'])
    out.append('last activity: ' + (' · '.join(last) if last else '—'))
    out.append('')
    tokens = []
    for cid in s['case_ids']:
        status, safety = case_status(run, cid)
        tokens.append(('!' if safety else '') + cid + ' ' + GLYPH[status])
    out.extend(wrap_tokens(tokens, width))
    out.append('legend: ✓ pass  ✗ fail  ? uncertain  ~ other  ◐ generated  ○ pending  leading ! = safety case')
    return '\n'.join(out)


def render_all(runs, width):
    out = ['JESSE LAB — ALL RUNS (%d)' % len(runs)]
    for run in runs:
        if run is None:
            continue
        s = summarise(run)
        prov = run['prov'] or {}
        head = run.get('legacy_head') or {}
        model = prov.get('jesse') or head.get('jesse') or '—'
        out.append('%-14s %-28s %-22s gen %d/%d eval %d/%d  P%d F%d U%d  %s' % (
            s['state'], str(run['dir']), str(model), s['generated'], s['total'],
            s['evaluated'], s['total'], s['verdicts']['PASS'], s['verdicts']['FAIL'],
            s['verdicts']['UNCERTAIN'], age_text(run['mtime'])))
    return '\n'.join(out)


def render_waiting(base, msg):
    return 'JESSE LAB — RUN DASHBOARD\n%s: %s' % (base, msg)


def main():
    p = argparse.ArgumentParser(description='Live read-only dashboard for Jesse Lab runs')
    p.add_argument('path', help='A run directory, or a directory containing run directories')
    p.add_argument('--interval', type=float, default=2.0, help='Refresh seconds (watch mode)')
    p.add_argument('--once', action='store_true', help='Render one frame and exit')
    p.add_argument('--all', action='store_true', help='Summarise every run found, one line each')
    a = p.parse_args()
    base = pathlib.Path(a.path)
    if base.is_file():
        base = base.parent

    def frame():
        width = min(110, max(40, _term_width()))
        runs = find_runs(base)
        if a.all:
            loaded = [load_run(d) for d in runs]
            loaded = [r for r in loaded if r is not None]
            if not loaded:
                return render_waiting(base, 'waiting for data — no readable runs yet'), None
            return render_all(loaded, width), tuple(run_mtime(d) for d in runs)
        if not runs:
            return render_waiting(base, 'waiting for data — no run files yet'), None
        target = runs[0]
        run = load_run(target)
        if run is None:
            return render_waiting(target, 'waiting for data — run files not readable yet'), run_mtime(target)
        note = None
        if len(runs) > 1:
            note = 'newest of %d runs' % len(runs)
        return render(run, width, note), run_mtime(target)

    if a.once:
        text, _ = frame()
        print(text)
        return
    # Watch mode: redraw on file change or interval, keep last good frame
    # if a read fails mid-rewrite.
    last_text = None
    sys.stdout.write('\033[?25l')
    try:
        while True:
            text, _stamp = frame()
            if text is not None:
                if last_text is not None and 'waiting for data' in text and 'waiting for data' not in last_text:
                    text = last_text  # transient read failure; keep last good frame
                last_text = text
                sys.stdout.write('\033[H\033[J' + text + '\n')
                sys.stdout.flush()
            time.sleep(max(0.2, a.interval))
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[?25h\n')
        sys.stdout.flush()


def _term_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


if __name__ == '__main__':
    main()
