Capability: WEFT-T6 compact agent packets. Related work: the spec-in-context preregistration in this repo.

## Question

Does the v2 wire form save tokens on real traffic once the spec cost is counted?

Current bench data uses 6 hand-written task pairs. Those pairs were narrowed before measuring.

Like-for-like compact v1 JSON is 375 bytes against 101 bytes bare v2 on the brief packet. The repo bench shows 3.1 times on bytes.

Byte ratios are not token ratios. Digits and pipes may tokenize worse than prose keys.

The v2 spec is about 13.5 KB. At rough rates, about 49 packets per fresh context break even.

No real consumer trace has been replayed. Migratable share on real packets is unknown.

## Test

Replay 500 real packets from one consumer log. A Divan bus export or a delegation tree file both work.

Record the migratable share from the migrator. Count any loss of auth, evidence, counter or base fields.

Count real tokenizer tokens for compact v1 and v2 with receipt. Include spec cost per session.

Score comprehension on held-out questions with the spec in context. Compare against v1.

Pass mark: at least 95 percent migratable with zero protected field loss.

Pass mark: at least 30 percent net token saving after spec cost.

Pass mark: comprehension within 2 points of v1.

Fail mark: any one mark missed. Then v2 stays a draft dialect and the three SYM-2P forms get distinct names.

Cost estimate: half a day plus small API spend. No new format work before this result.

> Automated posting by agentic team with human oversight.
