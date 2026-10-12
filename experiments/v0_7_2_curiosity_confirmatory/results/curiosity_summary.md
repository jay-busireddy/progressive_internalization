# v0.7.2.2 Synthetic Curiosity Summary

Rows analyzed: 192

- **gap_curiosity**: score 0.944, gap 1.000, select-recall 1.000, supported-bridge 1.000, eligible 3.00, pursued 3.00, prompt 471.0, query 19.3s, idle/ingest 0.0s
- **generic_seek**: score 0.667, gap 1.000, select-recall 0.667, supported-bridge 0.667, eligible 3.00, pursued 2.00, prompt 1873.0, query 19.4s, idle/ingest 41.2s
- **no_memory**: score 0.000, gap 1.000, select-recall 0.000, supported-bridge 0.000, eligible 3.00, pursued 0.00, prompt 259.0, query 17.6s, idle/ingest 0.0s
- **no_seek**: score 0.000, gap 1.000, select-recall 0.000, supported-bridge 0.000, eligible 3.00, pursued 0.00, prompt 387.0, query 21.1s, idle/ingest 0.0s
- **oracle_relevant**: score 1.000, gap 1.000, select-recall 0.000, supported-bridge 0.000, eligible 3.00, pursued 0.00, prompt 783.0, query 28.8s, idle/ingest 0.0s
- **oracle_seek_consolidated**: score 0.944, gap 1.000, select-recall 1.000, supported-bridge 1.000, eligible 3.00, pursued 3.00, prompt 471.0, query 9.5s, idle/ingest 0.0s
- **oracle_seek_direct**: score 1.000, gap 1.000, select-recall 1.000, supported-bridge 0.000, eligible 3.00, pursued 3.00, prompt 924.0, query 34.4s, idle/ingest 0.0s
- **random_seek**: score 0.125, gap 1.000, select-recall 0.125, supported-bridge 0.125, eligible 3.00, pursued 3.00, prompt 397.5, query 14.0s, idle/ingest 0.0s

Validity: no_memory=0.000; oracle_relevant=1.000; oracle_seek_direct=1.000; oracle_seek_consolidated=0.944.
Gap-curiosity detection=1.000; selection recall=1.000; supported post-learning bridge=1.000.
Gap - Random: delta +0.819, wins/ties/losses=24/0/0
Gap - Generic: delta +0.278, wins/ties/losses=20/4/0
Gap - NoSeek: delta +0.944, wins/ties/losses=24/0/0

**Verdict:** POSITIVE SYNTHETIC CURIOSITY MECHANISM; GAP-DRIVEN ALSO BEATS GENERIC SEEKING.

## Per-world scores
| scenario_id   |   seed |   gap_curiosity |   generic_seek |   no_memory |   no_seek |   oracle_relevant |   oracle_seek_consolidated |   oracle_seek_direct |   random_seek |
|:--------------|-------:|----------------:|---------------:|------------:|----------:|------------------:|---------------------------:|---------------------:|--------------:|
| syn01         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn01         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn02         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn02         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn03         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.333333 |
| syn03         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn04         |      0 |        0.666667 |       0.666667 |           0 |         0 |                 1 |                   0.666667 |                    1 |      0        |
| syn04         |      1 |        0.666667 |       0.666667 |           0 |         0 |                 1 |                   0.666667 |                    1 |      0.333333 |
| syn05         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn05         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.333333 |
| syn06         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.666667 |
| syn06         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn07         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn07         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn08         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn08         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.333333 |
| syn09         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.333333 |
| syn09         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.333333 |
| syn10         |      0 |        0.666667 |       0.666667 |           0 |         0 |                 1 |                   0.666667 |                    1 |      0        |
| syn10         |      1 |        0.666667 |       0.666667 |           0 |         0 |                 1 |                   0.666667 |                    1 |      0        |
| syn11         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn11         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn12         |      0 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0        |
| syn12         |      1 |        1        |       0.666667 |           0 |         0 |                 1 |                   1        |                    1 |      0.333333 |