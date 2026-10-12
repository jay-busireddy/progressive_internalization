# v0.7.2.1 — Synthetic Curiosity After Failed Recombination

This patch fixes the two failures exposed by the first v0.7.2 pilot:

1. **Gap discovery** is now a structured process-model completion task. The first idle phase must enumerate supported stages and explicitly record unresolved boundary links. It is not given the hidden rule or a future query.
2. **Post-learning consolidation** now receives the agent's own previously detected unresolved links plus newly acquired evidence and must explicitly resolve those links before creating an endpoint association.

The frozen v0.7.1 Dream experiment is unchanged elsewhere in the common repository.

## Methods

- `no_memory` — leakage control.
- `no_seek` — detects/replays but acquires no new evidence.
- `random_seek` — spends the same learning budget randomly.
- `generic_seek` — capable LLM chooses documents without an explicit stored gap representation.
- `gap_curiosity` — uses self-detected unresolved links to choose evidence, then runs a second idle consolidation.
- `oracle_seek_direct` — acquires the correct missing documents and answers directly from the complete process evidence; bypasses second consolidation. This proves selected evidence is sufficient.
- `oracle_seek_consolidated` — acquires the correct missing documents and runs the same second consolidation. This isolates whether reintegration works when document selection is perfect.
- `oracle_relevant` — exact transition-chain learnability control.

## Resource-limited curiosity

Detection does not automatically imply pursuit. The runner has:

- `--curiosity-budget N` — maximum candidate documents that may be acquired per world (default 3).
- `--min-gap-confidence X` — unresolved gaps below this confidence are stored but not pursued (default 0.50).

This is intentionally simple. It lets later experiments vary the resource budget without changing the curiosity mechanism.

## Pilot

```powershell
python -m pytest -q
python clean_results.py
python run_curiosity.py `
  --backend ollama `
  --model qwen2.5:7b `
  --pilot `
  --temperature 0.1 `
  --top-k 2 `
  --distractors 20 `
  --curiosity-budget 3 `
  --min-gap-confidence 0.50 `
  --num-ctx 8192
python analyze_curiosity.py
```

### Pilot gates

Do **not** run the full experiment unless approximately all of these hold:

- `no_memory <= 0.10`
- `oracle_relevant >= 0.80`
- `oracle_seek_direct >= 0.80`
- `oracle_seek_consolidated >= 0.80`
- `gap_curiosity gap_detection >= 0.75`
- `gap_curiosity selection_recall >= 0.75`
- `gap_curiosity supported_bridge_coverage >= 0.60`

Then inspect `gap_curiosity` against `random_seek`, `no_seek`, and especially `generic_seek`.

The generic baseline matters: if explicit gap-driven curiosity cannot beat generic document selection, the paper must not claim that the explicit curiosity representation itself is superior.
