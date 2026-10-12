# v0.7.2.2 — Synthetic Curiosity from Structural Knowledge Gaps

This revision fixes the two failures exposed by the v0.7.2.1 pilot without changing the frozen v0.7.1 Dream experiment.

## What changed

### 1. Gap detection is now structural and inspectable

The first idle phase no longer asks an LLM to rewrite the partial world model and hope that it verbalizes a missing link. The agent builds a process graph directly from its stored observations:

- process declarations establish the expected number of ordered stages;
- explicit stage facts populate known transitions;
- a missing internal stage between two supported neighboring stages becomes a **known unknown**;
- no future question and no candidate learning document is visible when the gap is created.

For example, if memory establishes stages 1, 2, and 4 of a four-stage process, the system can represent the missing stage-3 boundary as an unresolved relation between the output of stage 2 and the input of stage 4. It does **not** know the missing transformation yet.

This makes the curiosity trigger reproducible rather than prompt-fragile.

### 2. Second consolidation is additive, not generative rewriting

Newly acquired evidence is appended to the memory graph. The original observations are never regenerated or replaced.

After acquisition:

1. explicit new stage facts are parsed;
2. conflicting claims about the same stage are resolved by source authority;
3. the process is composed only if every declared stage is explicitly supported and the transitions connect;
4. the resulting endpoint bridge is stored separately with provenance to the declaration, source observations, and acquired document.

This directly addresses the v0.7.2.1 failure where `oracle_seek_direct=1.0` but `oracle_seek_consolidated=0.0`.

## Methods

- `no_memory` — leakage control.
- `no_seek` — gap exists but the agent acquires nothing.
- `random_seek` — spends the same document budget randomly.
- `generic_seek` — LLM chooses documents from partial memories without being given an explicit stored gap representation.
- `gap_curiosity` — uses the structurally detected known-unknown boundary to choose evidence, then performs additive consolidation.
- `oracle_seek_direct` — acquires the correct documents and answers directly from the complete evidence; proves acquired evidence is sufficient.
- `oracle_seek_consolidated` — acquires the correct documents and passes them through the same additive consolidation; isolates reintegration correctness.
- `oracle_relevant` — exact-chain learnability control.

## Resource-limited curiosity

Gap detection and gap pursuit remain separate:

- `--curiosity-budget N` limits how many documents may be acquired in one curiosity cycle.
- `--min-gap-confidence X` leaves low-confidence gaps in memory without spending resources on them.

The current structural gaps receive high confidence only when an explicit process-length declaration and neighboring supported stages expose the missing boundary.

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

## Pilot gates

Do not run the full experiment unless approximately all hold:

- `no_memory <= 0.10`
- `oracle_relevant >= 0.80`
- `oracle_seek_direct >= 0.80`
- `oracle_seek_consolidated >= 0.80`
- `gap_curiosity gap_detection >= 0.75`
- `gap_curiosity selection_recall >= 0.75`
- `gap_curiosity supported_bridge_coverage >= 0.60`

Then inspect the final transfer score against `no_seek`, `random_seek`, and especially `generic_seek`.

A positive curiosity claim requires more than perfect gap detection. The acquired evidence must improve later answering, and any advantage over `generic_seek` must be reported honestly.
