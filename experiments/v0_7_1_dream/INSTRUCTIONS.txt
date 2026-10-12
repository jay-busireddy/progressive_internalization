# Progressive Internalization v0.7.1 — Idle Dream/Recombination + Oracle Control

This is the final idle-consolidation test. It keeps the v0.7 Dream mechanism unchanged and adds one methodological control: `oracle_relevant`.

## What is being tested

The hypothesis is that an idle agent can selectively replay distributed memories, recombine them **before any future query exists**, store a genuinely new multi-hop association, and later answer a query that ordinary top-k retrieval cannot solve because the required facts are scattered through a noisy lifetime archive.

The three key matched conditions are:

- `fact_rag`: ordinary query-time top-k retrieval from the episodic archive.
- `replay_only`: query-independent idle selection of related original memories, but no new association is created.
- `dream_recombine`: uses the same idle-selected memories and appends new derived endpoint associations with provenance before any query arrives.

Additional controls:

- `no_memory`: leakage control.
- `oracle_relevant`: **learnability control**. Each question receives exactly the four relevant source observations, no distractors, and no derived relation.
- `full_history`: brute-force noisy-lifetime-context stress baseline. It is **not** a validity gate in v0.7.1.

## Why v0.7.1 changed the validity gate

In v0.7, Full History failed under the deliberately large noisy archive. That failure is part of the memory-pressure phenomenon being studied, so it should not be used to decide whether the synthetic rule chain itself is learnable.

v0.7.1 therefore uses:

- `no_memory <= 0.10`
- `oracle_relevant >= 0.80`

If either fails, do not interpret Dream vs Replay.

## Pre-query bridge metric

`bridge_coverage` is measured from Dream's stored derived relations **before query answering**. A covered question has a Dream-derived association containing both the question's upstream start symbol and correct downstream terminal symbol.

This distinguishes genuine idle consolidation from query-time reasoning.

## Install / validate

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

Expected: 5 tests pass.

## Pilot

```powershell
python clean_results.py

python run_synthetic.py `
  --backend ollama `
  --model qwen2.5:7b `
  --pilot `
  --temperature 0.1 `
  --top-k 2 `
  --distractors 60 `
  --num-ctx 8192

python analyze_dream.py
```

The pilot runs 2 worlds x 1 seed x 6 methods.

### Pilot gates

Proceed only if:

1. `no_memory <= 0.10`
2. `oracle_relevant >= 0.80`
3. mean Dream `bridge_coverage >= 0.60`
4. Dream materially beats Replay-only (target >= +0.08)

`full_history` may be low; report it as a noisy-context stress result, not a validity failure.

## Full run

Only after the pilot passes:

```powershell
python clean_results.py --keep-cache

python run_synthetic.py `
  --backend ollama `
  --model qwen2.5:7b `
  --scenarios all `
  --seeds 2 `
  --methods no_memory,fact_rag,replay_only,dream_recombine,oracle_relevant,full_history `
  --temperature 0.1 `
  --top-k 2 `
  --distractors 100 `
  --num-ctx 8192

python analyze_dream.py
```

## Final decision rule

The decisive comparison is `dream_recombine` vs `replay_only`, because both start from the same query-independent idle-selected source memories; only Dream is allowed to create new associations.

Continue only if:

- benchmark valid (`no_memory <= 0.10`, `oracle_relevant >= 0.80`),
- Dream - Replay-only >= +0.08,
- paired Dream wins > losses,
- mean pre-query bridge coverage >= 0.60,
- gains are not driven by one world.

Otherwise stop the mechanism.

## Files

- `run_synthetic.py` — runner
- `analyze_dream.py` — v0.7.1 analysis and validity gates
- `synthetic_learning/` — retrieval, replay, Dream, scoring, model adapter
- `synthetic_scenarios/` — invented worlds with per-question oracle source IDs
- `results/` — generated CSV, summary, caches
