# Curiosity, resource limits, and unknown unknowns

The v0.7.2.1 code intentionally separates **gap detection** from **gap pursuit**.

A detected gap is a known unknown. It may be retained cheaply without being pursued. Pursuit should be resource-gated by factors such as confidence that the gap is real, expected usefulness, task relevance, potential impact, novelty, and acquisition cost.

A simple decision rule for future work is:

`priority(g) = expected_information_gain * expected_utility * importance * confidence / estimated_cost`

Pursue only if `priority(g)` exceeds a threshold and a curiosity budget remains. Low-priority gaps can decay, merge with duplicates, or stay archived.

Unknown unknowns are different. By definition the agent cannot generate a gap for something outside its current ontology or observations. They require **exposure**: novel environments, distribution shifts, random/diversity-seeking exploration, contradictions, prediction failures, or other observations that do not fit the current model. Once such an event is encountered, the unknown unknown becomes a known unknown and the ordinary curiosity mechanism can act on it.

A future open-world architecture should therefore have two loops:

1. **Gap-driven exploitation:** pursue explicit known unknowns when their expected value exceeds cost.
2. **Budgeted exploration:** reserve a small resource share for diverse or surprising observations that can reveal unknown unknowns.

This file is design guidance, not a tested claim in v0.7.2.1.
