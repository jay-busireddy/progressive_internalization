# Experiment map

## v0.7.1 — Dream/Recombination (frozen)

Question: can query-independent idle recombination create useful bridge associations under retrieval starvation?

Primary comparison: `dream_recombine` vs `replay_only`.

## v0.7.2.2 — Synthetic curiosity after incomplete recombination

Question: when an internal process model exposes a specific missing relation, can a resource-limited agent use that known unknown to acquire the right evidence, integrate it additively, and improve a later unseen query?

Causal decomposition:

1. `oracle_relevant` — is the reasoning task solvable?
2. `oracle_seek_direct` — is perfect newly acquired evidence sufficient?
3. `oracle_seek_consolidated` — can additive consolidation preserve and use perfect acquired evidence?
4. `gap_curiosity` — can a structurally detected gap drive useful evidence acquisition and integration?
5. `generic_seek` — does explicit gap representation provide value beyond generic LLM document selection?
6. `random_seek` / `no_seek` — budget and acquisition baselines.

### Important methodological change from v0.7.2.1

Gap detection is no longer an LLM text-generation task. The agent builds an explicit process graph from observations and identifies missing internal stages as known unknowns. This uses no future questions and no candidate documents.

Post-learning consolidation is also non-destructive: acquired facts are appended, authority conflicts are resolved, and endpoint bridges are composed only from fully supported stage chains with provenance.

This makes the experiment about the value of a represented knowledge gap, rather than the reliability of an LLM rewriting its own memory state.

Resource control remains explicit: `--curiosity-budget` caps acquisitions and `--min-gap-confidence` prevents weak gaps from consuming the budget.
