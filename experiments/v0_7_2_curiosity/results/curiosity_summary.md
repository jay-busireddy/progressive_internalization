# v0.7.2.2 Synthetic Curiosity Summary

Rows analyzed: 96

- **gap_curiosity**: score 1.000, gap 1.000, select-recall 1.000, supported-bridge 1.000, eligible 3.00, pursued 3.00, prompt 467.0, query 18.0s, idle/ingest 0.0s
- **generic_seek**: score 0.556, gap 1.000, select-recall 0.556, supported-bridge 0.556, eligible 3.00, pursued 1.67, prompt 1730.7, query 17.6s, idle/ingest 42.0s
- **no_memory**: score 0.000, gap 1.000, select-recall 0.000, supported-bridge 0.000, eligible 3.00, pursued 0.00, prompt 255.0, query 14.0s, idle/ingest 0.0s
- **no_seek**: score 0.000, gap 1.000, select-recall 0.000, supported-bridge 0.000, eligible 3.00, pursued 0.00, prompt 383.0, query 20.7s, idle/ingest 0.0s
- **oracle_relevant**: score 1.000, gap 1.000, select-recall 0.000, supported-bridge 0.000, eligible 3.00, pursued 0.00, prompt 779.0, query 28.5s, idle/ingest 0.0s
- **oracle_seek_consolidated**: score 1.000, gap 1.000, select-recall 1.000, supported-bridge 1.000, eligible 3.00, pursued 3.00, prompt 467.0, query 8.7s, idle/ingest 0.0s
- **oracle_seek_direct**: score 1.000, gap 1.000, select-recall 1.000, supported-bridge 0.000, eligible 3.00, pursued 3.00, prompt 920.0, query 31.8s, idle/ingest 0.0s
- **random_seek**: score 0.306, gap 1.000, select-recall 0.306, supported-bridge 0.306, eligible 3.00, pursued 3.00, prompt 408.7, query 18.6s, idle/ingest 0.0s

Validity: no_memory=0.000; oracle_relevant=1.000; oracle_seek_direct=1.000; oracle_seek_consolidated=1.000.
Gap-curiosity detection=1.000; selection recall=1.000; supported post-learning bridge=1.000.
Gap - Random: delta +0.694, wins/ties/losses=12/0/0
Gap - Generic: delta +0.444, wins/ties/losses=12/0/0
Gap - NoSeek: delta +1.000, wins/ties/losses=12/0/0

**Verdict:** POSITIVE SYNTHETIC CURIOSITY MECHANISM; GAP-DRIVEN ALSO BEATS GENERIC SEEKING.

## Per-world scores
| scenario_id   |   seed |   gap_curiosity |   generic_seek |   no_memory |   no_seek |   oracle_relevant |   oracle_seek_consolidated |   oracle_seek_direct |   random_seek |
|:--------------|-------:|----------------:|---------------:|------------:|----------:|------------------:|---------------------------:|---------------------:|--------------:|
| syn01         |      0 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn01         |      1 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn02         |      0 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn02         |      1 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn03         |      0 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.666667 |
| syn03         |      1 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn04         |      0 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn04         |      1 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn05         |      0 |               1 |       0        |           0 |         0 |                 1 |                          1 |                    1 |      0        |
| syn05         |      1 |               1 |       0        |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |
| syn06         |      0 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0        |
| syn06         |      1 |               1 |       0.666667 |           0 |         0 |                 1 |                          1 |                    1 |      0.333333 |