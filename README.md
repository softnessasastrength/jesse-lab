# Jesse Lab

Local experimental baseline and one-step LoRA smoke test for an Apple Silicon Mac. Synthetic examples only. Not a medical device or validated safety system. Human review of all safety results is mandatory. Never put private archive data, model outputs, or adapter weights in a public repository. Adapters can memorize training data.

## Baseline

Install and start Ollama, and pull the desired model. From this directory:

```sh
python3 bench.py --jesse gpt-oss:latest --judge gpt-oss:latest --out runs/baseline
```

Generation and evaluation run in separate phases and request model unload after each request. This is slower but limits residency; Ollama can have other models loaded—check `ollama ps`. The judge is advisory, can miss safety failures, and using the same model for both roles reduces independence. Edit prompts/jesse.txt and cases.jsonl to tailor the baseline. The bundled prompt is a concise local approximation, not a validated reproduction of the plugin. Inspect prompts/jesse-source.md for earlier source instructions. Serious cases receive no jokes. Review report.md and results.json. Raw inputs and responses are stored locally; use encrypted storage for sensitive data.

## Dashboard

Watch a run live from another terminal:

```sh
python3 dashboard.py runs/baseline
```

The dashboard is read-only. It shows the run's script, runtime, model, and judge from its provenance; generation and evaluation progress; PASS / FAIL / UNCERTAIN tallies as evaluations land, with failed safety cases named; the most recent case activity; and a per-case status grid. It tolerates files caught mid-rewrite and keeps the last good frame instead of crashing. Point it at a directory of runs and add `--all` for a one-line summary per run, or `--once` to print a single frame and exit. Runs written before checkpointing carry no provenance and are labelled PARTIAL-LEGACY. Tallies are the judge's, not a verdict; human review is still required.

## Training smoke test

Install Xcode command line tools and Python 3, then `bash setup.sh`. This downloads packages and records resolved versions but is not a lockfile. Obtain a compatible MLX checkpoint separately; Ollama's model is not automatically an MLX checkpoint. Ensure enough SSD space and stop Ollama models first. Then:

```sh
MODEL=/absolute/path/to/mlx-checkpoint bash smoke.sh
# Or MODEL=owner/compatible-mlx-model bash smoke.sh (downloads from Hugging Face)
```

This runs one step on synthetic data only and logs the result under ignored runs/. A model name may cause a large download. Memory requirements and compatibility are unverified on your Mac. If it fails, inspect train.log; upstream gpt-oss LoRA bug https://github.com/ml-explore/mlx-lm/issues/1814 is closed but that alone does not establish that your installed release includes its fix. Check upstream documentation and versions. No automatic long training or promotion occurs. Don't train a real adapter until you have reviewed, consented data and meaningful held-out safety tests.

`python3 prepare.py private/data.jsonl private/prepared` validates approved records and exports MLX chat-format splits. Copy the synthetic file to understand the schema. Group related conversations in one split; near-duplicate detection is manual. This export has not been verified against a real Mac training run. Real data and runs are intentionally gitignored.

For SSH, keep the Mac awake using a temporary `caffeinate -i` session, and use tmux or another session manager to survive disconnects. Verify SSH before logging out. FileVault can require local unlock after reboot. Never disable core services or security protections for RAM.

## Limits

This is a runnable prototype, not a trained model or proven safety gate. Ollama baseline and MLX adapter paths are separate; adapter inference and automatic comparison are implemented, but not yet validated on the target Mac. Training, GPU usage, and speed have not been tested on your machine. No data is uploaded by the bench; pip and model downloads require network access.
