# Experiment C freeze decision: do not freeze the current draft

Decision date: 2026-11-16. Owner: amp-vela. This note supersedes the design in `PREREG-C.md` until a revised protocol is frozen.

## Finding

The current transformer harness cannot decide the claim as drafted.

In `tf_common.batch`, the six operand tokens are drawn independently of the task. The first token is the only task information in the sequence. Remove or falsify that token and the remaining sequence carries no task information at all. An endogenous receptor cannot recover it, because its activations are also a function of that same remaining sequence.

The converse also fails. If a revised task makes the operand distribution depend on the task, an outside router can learn that same statistic from the raw sequence. That becomes a matched-budget learnability comparison. It cannot support the stronger claim that no input-output router can be written.

So the draft conflates three different claims:

1. Context is absent. Then every arm is at chance.
2. Context is a function of the current input. Then a sufficiently capable input router can learn it.
3. Context lives in episode history or host state that the router does not receive. Then the test is about an access boundary, and that boundary must be stated as part of the claim.

Only the third form can carry the novelty stake in issue 17. The current stateless harness does not implement it.

## Revised Experiment C2 (not yet frozen)

Use an episodic sequence. A demonstration segment shows one operand set and its transformed output. A later query segment gives new operands drawn independently of the demonstrated operation. There is no task token.

The host is trained on demonstration-to-query episodes for COPY and ADD3. The donor also knows MUL5. The packet is distilled for MUL5 and reads query-position activations after the host has attended to the demonstration segment.

The outside router receives the query operands only. It does not receive the demonstration segment, host activations, or an episode-conditioned host output. By construction, the query operand distribution is independent of the demonstrated operation.

Required arms:

1. Internal packet with full host forward context.
2. Query-only outside router at a matched training and compute budget.
3. External adapter under the same query-only interface.
4. Always-on packet control.
5. Full-transcript router as a positive control. It receives the demonstration and should pass. This arm proves the boundary is access, not missing information in the episode.

Required validity checks before any confirmatory seed:

1. A query-only classifier trained to predict the demonstrated operation stays near chance on fresh episodes.
2. A demonstration-only classifier can predict the operation. This proves the episode carries the context.
3. Host native performance is measured with the packet gate forced open and closed.
4. Packet, router and adapter budgets are recorded in parameters, donor queries, training rows and evaluated rows.

## What a pass would and would not show

A pass would show an integration advantage: behaviour carried inside the host can use episode context that a stateless outside router never receives. That is relevant to persistent digital intelligence, where internal context is not automatically exported to every tool.

A pass would not show that no outside system can solve the task. Give the router the transcript or the activations and it may match. The claim must keep that access boundary in its first sentence.

## Recommendation

Do not freeze `PREREG-C.md` in its current form. Build the episodic harness and the two validity classifiers first. Freeze C2 only after a pilot shows the query-only arm at chance and the full-transcript arm passing.

If the team prefers the cheaper matched-budget learnability test, run it under that name. Do not present it as the decisive no-switch test.

## Disclosure

Written by an AI agent session with human oversight. No new run is claimed here. The impossibility reading for the current harness follows from its sampler code.
