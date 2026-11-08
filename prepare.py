#!/usr/bin/env python3
import sys, json, pathlib, hashlib

def main():
    if len(sys.argv) != 3:
        raise ValueError('Usage: python3 prepare.py INPUT.jsonl OUTPUT_DIR')
    source, dest = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    rows, groups, hashes, ids = {s: [] for s in ('train','valid','test')}, {}, {}, set()
    for n, line in enumerate(source.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip(): continue
        r = json.loads(line); split = r.get('split'); group = r.get('group'); ident = r.get('id')
        if split not in rows or not isinstance(group,str) or not group or not isinstance(ident,str) or not ident: raise ValueError(f'line {n}: invalid id/group/split')
        if ident in ids: raise ValueError(f'line {n}: duplicate id')
        ids.add(ident)
        if r.get('consent') != 'approved' or not r.get('provenance'): raise ValueError(f'line {n}: approval and provenance required')
        messages = r.get('messages')
        if not isinstance(messages,list) or len(messages)<2 or messages[-1].get('role') != 'assistant': raise ValueError(f'line {n}: messages must end in assistant')
        for m in messages:
            if not isinstance(m,dict) or m.get('role') not in ('system','user','assistant') or not isinstance(m.get('content'),str) or not m['content'].strip(): raise ValueError(f'line {n}: invalid message')
        if not any(m['role']=='user' for m in messages): raise ValueError(f'line {n}: missing user')
        if group in groups and groups[group] != split: raise ValueError(f'line {n}: group crosses splits')
        groups[group] = split
        key=hashlib.sha256(json.dumps(messages,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if key in hashes: raise ValueError(f'line {n}: duplicate conversation in {hashes[key]}')
        hashes[key]=split
        rows[split].append({'messages':messages})
    if any(not v for v in rows.values()): raise ValueError('All three splits need at least one example')
    if dest.exists() and any(dest.iterdir()): raise ValueError('Output directory must be empty to prevent accidental overwrite')
    dest.mkdir(parents=True,exist_ok=True)
    for split, examples in rows.items():
        (dest/(split+'.jsonl')).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in examples),encoding='utf-8')
    print('Prepared:', ', '.join(f'{s}={len(v)}' for s,v in rows.items()))
if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, json.JSONDecodeError) as exc: print(f'Error: {exc}',file=sys.stderr); sys.exit(1)
