# v0.7.1 Idle Dream/Recombination Summary

Rows analyzed: 144

- **dream_recombine**: score 0.264, memory 110.7, prompt 1247.2, query 13.8s, ingest 59.4s, bridge 0.139
- **fact_rag**: score 0.306, memory 108.0, prompt 482.5, query 15.2s, ingest 0.0s
- **full_history**: score 0.319, memory 2134.0, prompt 5293.4, query 128.2s, ingest 0.0s
- **no_memory**: score 0.000, memory 6.0, prompt 262.0, query 10.8s, ingest 0.0s
- **oracle_relevant**: score 1.000, memory 207.0, prompt 730.8, query 20.3s, ingest 0.0s
- **replay_only**: score 0.333, memory 108.0, prompt 482.2, query 9.9s, ingest 0.0s

Validity: no_memory=0.000 (<=0.10), oracle_relevant=1.000 (>=0.80).
Full-history stress baseline: 0.319 (not a validity gate).
Dream - Fact-RAG: -0.042
Dream - Replay-only: -0.069
Dream vs Replay paired wins/ties/losses: 1/16/7
Mean Dream bridge coverage before query: 0.139

**Verdict:** STOP: offline recombination does not materially beat selective replay under the same retrieval budget.

## Per-world scores
| scenario_id   |   dream_recombine |   fact_rag |   full_history |   no_memory |   oracle_relevant |   replay_only |
|:--------------|------------------:|-----------:|---------------:|------------:|------------------:|--------------:|
| syn01         |             0.333 |      0.333 |          0.667 |           0 |                 1 |         0.333 |
| syn02         |             0.333 |      0.333 |          0.5   |           0 |                 1 |         0.333 |
| syn03         |             0     |      0.333 |          0.333 |           0 |                 1 |         0.333 |
| syn04         |             0     |      0     |          0.333 |           0 |                 1 |         0.333 |
| syn05         |             0.333 |      0.333 |          0.333 |           0 |                 1 |         0.333 |
| syn06         |             0     |      0.333 |          0.333 |           0 |                 1 |         0.333 |
| syn07         |             0.333 |      0.333 |          0     |           0 |                 1 |         0.333 |
| syn08         |             0.333 |      0.333 |          0.333 |           0 |                 1 |         0.333 |
| syn09         |             0.333 |      0.333 |          0     |           0 |                 1 |         0.333 |
| syn10         |             0.667 |      0.333 |          0.333 |           0 |                 1 |         0.333 |
| syn11         |             0.167 |      0.333 |          0.333 |           0 |                 1 |         0.333 |
| syn12         |             0.333 |      0.333 |          0.333 |           0 |                 1 |         0.333 |

## No-memory leakage by world
- syn01: 0.000
- syn02: 0.000
- syn03: 0.000
- syn04: 0.000
- syn05: 0.000
- syn06: 0.000
- syn07: 0.000
- syn08: 0.000
- syn09: 0.000
- syn10: 0.000
- syn11: 0.000
- syn12: 0.000

## Oracle-relevant learnability by world
- syn01: 1.000
- syn02: 1.000
- syn03: 1.000
- syn04: 1.000
- syn05: 1.000
- syn06: 1.000
- syn07: 1.000
- syn08: 1.000
- syn09: 1.000
- syn10: 1.000
- syn11: 1.000
- syn12: 1.000