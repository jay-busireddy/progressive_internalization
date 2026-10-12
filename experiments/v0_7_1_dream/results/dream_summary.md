# v0.7.1 Idle Dream/Recombination Summary

Rows analyzed: 96

- **dream_recombine**: score 0.354, memory 102.3, prompt 1397.2, query 24.0s, ingest 116.6s, bridge 0.292
- **fact_rag**: score 0.000, memory 99.8, prompt 521.5, query 31.9s, ingest 0.0s
- **full_history**: score 0.542, memory 2125.0, prompt 5582.5, query 371.3s, ingest 0.0s
- **no_memory**: score 0.000, memory 6.0, prompt 286.0, query 48.6s, ingest 0.0s
- **oracle_relevant**: score 1.000, memory 207.0, prompt 842.9, query 51.3s, ingest 0.0s
- **replay_only**: score 0.208, memory 92.6, prompt 515.5, query 35.9s, ingest 0.0s

Validity: no_memory=0.000 (<=0.10), oracle_relevant=1.000 (>=0.80).
Full-history stress baseline: 0.542 (not a validity gate).
Dream - Fact-RAG: +0.354
Dream - Replay-only: +0.146
Dream vs Replay paired wins/ties/losses: 3/12/1
Mean Dream bridge coverage before query: 0.292

**Verdict:** AMBIGUOUS: inspect paired worlds; effect is between stop/continue thresholds.

## Per-world scores
| scenario_id   |   dream_recombine |   fact_rag |   full_history |   no_memory |   oracle_relevant |   replay_only |
|:--------------|------------------:|-----------:|---------------:|------------:|------------------:|--------------:|
| syn01         |             0     |          0 |          1     |           0 |                 1 |         0     |
| syn02         |             0     |          0 |          0     |           0 |                 1 |         0     |
| syn03         |             0.667 |          0 |          1     |           0 |                 1 |         0.333 |
| syn04         |             0.333 |          0 |          1     |           0 |                 1 |         0.333 |
| syn05         |             1     |          0 |          0.667 |           0 |                 1 |         0     |
| syn06         |             0.167 |          0 |          0     |           0 |                 1 |         0.333 |
| syn07         |             0.333 |          0 |          0.333 |           0 |                 1 |         0.333 |
| syn08         |             0.333 |          0 |          0.333 |           0 |                 1 |         0.333 |

## No-memory leakage by world
- syn01: 0.000
- syn02: 0.000
- syn03: 0.000
- syn04: 0.000
- syn05: 0.000
- syn06: 0.000
- syn07: 0.000
- syn08: 0.000

## Oracle-relevant learnability by world
- syn01: 1.000
- syn02: 1.000
- syn03: 1.000
- syn04: 1.000
- syn05: 1.000
- syn06: 1.000
- syn07: 1.000
- syn08: 1.000