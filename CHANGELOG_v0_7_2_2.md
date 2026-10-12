# v0.7.2.2 changelog

- Kept v0.7.1 Dream/Recombination frozen.
- Preserved the previous v0.7.2.1 curiosity implementation under `experiments/v0_7_2_1_curiosity/`.
- Replaced LLM-dependent gap-state rewriting with deterministic structural process-graph construction from stored observations only.
- Missing internal stages are represented as explicit known-unknown boundaries before any candidate document or future query is visible.
- Replaced generative second consolidation with additive deterministic graph composition.
- Newly acquired facts are appended; original episodic memories are never rewritten.
- Source authority resolves competing stage claims.
- Derived endpoint bridges require a complete connected stage chain and retain evidence provenance.
- Retained resource gating through `--curiosity-budget` and `--min-gap-confidence`.
- Retained `oracle_seek_direct` and `oracle_seek_consolidated` controls.
- Added regression tests for structural gap discovery and provenance-backed additive bridge creation.
- v0.7.1 tests: 5/5 passing. v0.7.2.2 tests: 7/7 passing.
