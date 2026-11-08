# Muse handoff — Jesse Lab

- **AUTHOR:** Ember (Muse), building on GPT-6's handoff of 2026-11-08 (preserved in git history on `main`).
- **AUTHORITY:** Branden's instruction of 2026-11-08 to take the baton from GPT-6 and work in this repository so he can pull as the work lands.
- **EVIDENCE:** The repository contents as verified in Ember's reconciliation of 2026-11-08, and the commits on branch `baton_muse`.
- **REQUESTED_ACTION:** Branden pulls branch `baton_muse` and reviews. No merge to `main` without his word.

## Repository visibility — corrected

GPT-6's handoff opened its status section with the words "Private repository." That was wrong: this repository is **public**. Branden ruled on 2026-11-08 that it stays public during this skeleton phase — workflow code, synthetic cases, harness work, documentation — and that he will flip it to private when substantive material arrives. Standing rule while it is public: **no archive data, no autobiographical material, no real conversation content, no adapter weights, and no real run results in this repo.** Those live on the Mac and in the gitignored paths (`runs/`, `private/`).

## Intent

*(From GPT-6's handoff, preserved.)* Branden wants a faithful, emotionally precise Jesse and a local drill-sergeant evaluator on a 16 GB M4 Mac mini. Safety is non-negotiable: respect agency, corrections, uncertainty and privacy; prevent dependency, false authority and unsafe crisis handling. Humor targets model behavior, not the user; drop it in serious cases. His archive is private, consented, curated source material; never turn old assistant interpretations into user facts.

## Current status

*(From GPT-6's handoff; the repo-side contents were verified by Ember on 2026-11-08.)* The repo has the Ollama baseline bench, synthetic test cases, dataset preparation (`prepare.py`), a one-step MLX LoRA smoke test, and initial MLX adapter evaluation and comparison scripts. GPT-6 reports that Branden cloned and ran the baseline successfully with `gpt-oss:latest` and that the results are on his Mac. GitHub does not hold the private archive or generated results, and Ember has not independently verified the Mac-side baseline results — verifying them is an outstanding item below.

Model tag note *(GPT-6)*: the installed model tag is `gpt-oss:latest`, not necessarily `gpt-oss:20b`. *(Resolution — Ember, 2026-11-08, at Branden's instruction: `bench.py` defaults and the README baseline command have been aligned to `gpt-oss:latest` on this branch, so the defaults now match the installed tag. Passing the tag explicitly remains harmless.)*

## Commands

*(From GPT-6's handoff.)*
`python3 bench.py --jesse gpt-oss:latest --judge gpt-oss:latest --out runs/baseline`.
`bash setup.sh` installs MLX dependencies; `MODEL=/path/to/compatible-mlx-checkpoint bash smoke.sh` runs a one-step synthetic smoke test. Requires a compatible separately downloaded MLX checkpoint, not the Ollama model.
After a real adapter exists: `.venv/bin/python adapter_eval.py --model /path/to/base --adapter /path/to/adapter --judge gpt-oss:latest --out runs/adapter` then `python3 compare.py runs/baseline/results.json runs/adapter/results.json --out runs/comparison.md`.

New on `baton_muse`: both benches accept `--temperature`, `--seed` and `--revision` (bench.py also `--num-ctx`), and GPT-6's `--case` repeat-filter in bench.py is preserved. Rerunning a bench with the same `--out` resumes from `checkpoint.json` instead of failing; a legacy `results.json` with no `checkpoint.json` beside it is still refused, so old outputs are never silently overwritten. Note: run identity includes the script version (now `2.1_muse` after the reconciliation in item 6 below), so a checkpoint written by the `2.0_muse` scripts is refused on resume — deliberate: the code changed under it.

## What changed on this branch

*(Ember, 2026-11-08.)*

1. **Checkpointing + interruption recovery** in `bench.py` and `adapter_eval.py`. Progress is written atomically (temp file + rename, mode 0600) to `checkpoint.json` and `results.json` after every generation and every evaluation, so an interruption loses at most the case in flight. A rerun with the same `--out` skips completed cases when the recorded run identity (script, models, sampling settings, case-file SHA-256) matches, and refuses if it does not. `adapter_eval.py` loads the MLX model only when generation work remains, so an evaluation-only resume never touches the checkpoint or adapter. The checkpoint/resume logic was exercised offline with stubbed model calls before pushing; live execution on the Mac is still outstanding.
2. **Determinism + provenance.** Ollama sampling (`temperature`, `seed`, `num_ctx`) is now explicit in `bench.py` rather than buried in the request builder, and `adapter_eval.py` passes an explicit MLX sampler (`make_sampler(temp=...)`) and seeds `mlx.random` via `--temperature`/`--seed` (defaults: greedy, seed 0). Both scripts record a provenance block in `results.json`: script name and version, UTC timestamp, runtime (`ollama` / `mlx`), model and judge identifiers as passed, sampling parameters, case-file SHA-256 with case count and IDs, a `complete` flag, and a `--revision` free-text field for package/model revision notes. `compare.py` is **unchanged**: it reads only the `results` array, whose per-case schema is unchanged, so it reads old- and new-format results files alike (verified against both).
3. **New synthetic case files.** `cases_regression.jsonl` (10 invented cases) expands the crisis and dependence cases from `cases.jsonl`: crisis in indirect, third-person, past-tense, ambiguous and withdrawal framings; dependence as secrecy pact, human replacement, multi-turn escalation, false authority and permanence promise. `cases_holdout.jsonl` (7 invented cases, each marked `"holdout": true` — the one deliberate schema addition) spans the existing case kinds plus crisis and dependence. **Holdout cases are for evaluation only; never tune against them.** Both files use the existing `cases.jsonl` schema (`id`, `messages`, `expect`, `safety`).
4. **This handoff**, replacing GPT-6's, with the four-field header and the visibility correction above.
5. **Model-tag alignment** *(Ember, 2026-11-08, at Branden's instruction).* `bench.py`'s `--jesse`/`--judge` defaults and the README baseline command changed from `gpt-oss:20b` to `gpt-oss:latest`, matching the tag installed on the Mac; `adapter_eval.py`'s `--judge` default already said `gpt-oss:latest`. In the same commit, the README's stale Limits claim that adapter inference and automatic comparison were 'not yet implemented' was corrected: both are implemented, not yet validated on the target Mac.
6. **Reconciliation up to main `d7c85007`** *(Ember, 2026-11-08, at Branden's instruction to make sure the tooling is up to date).* GPT-6 advanced main by one commit after this branch forked ('Preserve diagnostics and fail empty responses'); main and the branch are now unified on this branch. Resolutions, one line each:
   - *bench.py — diagnostics vs checkpointing* → both: main's `request_chat()` diagnostics (`generation_metadata`/`judge_metadata`, including thinking fields), `evaluation_status`, empty-response auto-FAIL, empty-judge UNCERTAIN fallback and `--case` filter are kept, inside the branch's checkpoint/resume/provenance harness; `results.json` now carries main's top-level `status` alongside the provenance `complete` flag.
   - *`chat()` signature conflict* (main: two arguments; branch: three, with an explicit sampling dict) → sampling is now an optional argument falling back to the bench defaults; `adapter_eval.py` calls `request_chat()` directly so judge diagnostics are recorded there too.
   - *adapter_eval.py evaluation* → gained the main-bench semantics: empty candidate = automatic FAIL, empty judge = UNCERTAIN fallback, plus `evaluation_status` and `judge_metadata` on every judged row.
   - *report.md* → main's format (including the Generation metadata section) kept, but written atomically, so rerunning a completed run regenerates the report instead of failing on `O_EXCL`.
   - *README* → main changed nothing in it since the fork; the branch version stands.
   - *Version strings* → both benches are now `2.1_muse` (see the resume note under Commands).
   No CLI flags were removed or renamed: `--temperature`/`--seed`/`--num-ctx`/`--revision` (branch) and `--case` (main) coexist in bench.py. `dashboard.py` and `compare.py` needed no changes — the reconciled schema keeps every field they read, verified offline against reconciled-format, main-format and legacy-format fixtures.

## Limitations and next work

*(GPT-6's limitations, preserved and updated.)* Adapter inference and training are untested on the target Mac and depend on the current MLX-LM API (including the `make_sampler` sampler interface used for `--temperature`), checkpoint format, chat template and memory. The checkpointing removes the old lose-everything failure, but nothing here has run against a real model yet. Baseline is Ollama while the candidate uses MLX; quantization, sampling and runtime differences confound attribution — validate with the same MLX base and settings before drawing conclusions. A one-step synthetic adapter is not Jesse. The same-model judge is not independent and may be wrong; passing scores do not certify safety. No automatic promotion. Avoid committing archive data, logs, or adapter weights; adapters can memorize data. Preserve user voice and distinguish archival facts from assistant interpretations.

Still to add: a real training workflow, curated holdout coverage beyond the starter set above, explicit human review of every safety result, and deterministic settings anywhere they are still implicit.

**Mac-side work still outstanding:** run `bash setup.sh`; obtain a compatible MLX checkpoint; run `smoke.sh`; train a real adapter on reviewed, consented data; run `adapter_eval.py` against it and `compare.py` on the real outputs; do the same-runtime (MLX-vs-MLX) validation run; verify the baseline results GPT-6 reports are on the Mac.

## Known baseline behavior

- *(GPT-6, superseded on this branch.)* "The bench requests Ollama unload after every call and only saves after both phases, so interruption loses progress." The unload-after-every-call behaviour is unchanged; the save behaviour is fixed by the checkpointing above.
- *(GPT-6.)* The installed model tag is `gpt-oss:latest`, not necessarily `gpt-oss:20b`.
- `adapter_eval.py` imports `request_chat()` and `ROOT` from `bench.py` (bench.py's `chat()` remains available, with an optional sampling argument falling back to the bench defaults). Keep the two files in step when editing either.
