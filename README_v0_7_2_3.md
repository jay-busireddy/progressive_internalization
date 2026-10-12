# Progressive Internalization v0.7.2.3 Common Repository

This repository keeps the original positive experiments and adds a frozen confirmatory replication set.

## Experiment folders

- `experiments/v0_7_1_dream/` — original v0.7.1 Dream/Recombination experiment and development worlds. Do not modify.
- `experiments/v0_7_2_curiosity/` — original v0.7.2.2 Curiosity experiment and development worlds. Do not modify.
- `experiments/v0_7_1_dream_confirmatory/` — exact same Dream code, 12 newly generated untouched worlds.
- `experiments/v0_7_2_curiosity_confirmatory/` — exact same Curiosity code, 12 newly generated untouched worlds.
- `experiments/v0_7_2_1_curiosity/` — retained historical failed/intermediate curiosity version.

The confirmatory JSON files were frozen before model evaluation. Their SHA-256 hashes are in `CONFIRMATORY_WORLD_MANIFEST.md`.

## Recommended second model

Use Ollama `mistral:instruct` as the non-Qwen replication model.

```powershell
ollama pull mistral:instruct
```

## Run the complete four-cell replication

See:
- `RUN_MISTRAL_CONFIRMATORY.ps1` for the untouched-world Mistral tests.
- `RUN_QWEN_CONFIRMATORY.ps1` for the untouched-world Qwen tests.
- `RUN_MISTRAL_ORIGINAL.ps1` for the same original worlds with Mistral.

Do not tune prompts, thresholds, temperatures, retrieval budgets, or world JSONs after observing confirmatory results.

## Frozen confirmatory settings

Dream:
- 12 worlds
- 2 seeds
- top-k = 2
- distractors = 100
- temperature = 0.1
- num_ctx = 8192

Curiosity:
- 12 worlds
- 2 seeds
- top-k = 2
- distractors = 40
- curiosity budget = 3
- min gap confidence = 0.50
- temperature = 0.1
- num_ctx = 8192
