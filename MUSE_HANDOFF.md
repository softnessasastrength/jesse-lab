# Muse handoff — Jesse Lab

## Intent
Branden wants a faithful, emotionally precise Jesse and a local drill-sergeant evaluator on a 16 GB M4 Mac mini. Safety is non-negotiable: respect agency, corrections, uncertainty and privacy; prevent dependency, false authority and unsafe crisis handling. Humor targets model behavior, not the user; drop it in serious cases. His archive is private, consented, curated source material; never turn old assistant interpretations into user facts.

## Current status
Private repository has Ollama baseline bench, synthetic test cases, dataset preparation, one-step MLX LoRA smoke test, initial MLX adapter evaluation and comparison scripts. Branden cloned and ran the baseline successfully with `gpt-oss:latest`; results are on his Mac. GitHub does not hold the private archive or generated results.

## Commands
`python3 bench.py --jesse gpt-oss:latest --judge gpt-oss:latest --out runs/baseline`.
`bash setup.sh` installs MLX dependencies; `MODEL=/path/to/compatible-mlx-checkpoint bash smoke.sh` runs a one-step synthetic smoke test. Requires a compatible separately downloaded MLX checkpoint, not the Ollama model.
After a real adapter exists: `.venv/bin/python adapter_eval.py --model /path/to/base --adapter /path/to/adapter --judge gpt-oss:latest --out runs/adapter` then `python3 compare.py runs/baseline/results.json runs/adapter/results.json --out runs/comparison.md`.

## Limitations and next work
Adapter inference and training are untested on target Mac and depend on current MLX-LM API, checkpoint format, chat template and memory. Baseline is Ollama while candidate uses MLX; quantization, sampling and runtime differences confound attribution. Validate with the same MLX base and settings before drawing conclusions. A one-step synthetic adapter is not Jesse. Add reliable progress checkpoints and interruption recovery, deterministic settings where feasible, provenance and package/model revision metadata, curated holdout cases, explicit human review, crisis and dependency regression tests, and a real training workflow. The same-model judge is not independent and may be wrong; passing scores do not certify safety. No automatic promotion. Avoid committing archive data, logs, or adapter weights; adapters can memorize data. Preserve user voice and distinguish archival facts from assistant interpretations.

## Known baseline behavior
The bench requests Ollama unload after every call and only saves after both phases, so interruption loses progress. The installed model tag is `gpt-oss:latest`, not necessarily `gpt-oss:20b`.
