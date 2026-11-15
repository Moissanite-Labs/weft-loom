# Committed Behaviour Change, design v1

Owner: amp-vela. Proposal: weft-loom issue 17. This file pins the semantics that the code in this folder implements. Anything not pinned here is not claimed.

## The object

A Committed Behaviour Change (CBC) is one record with these fields:

- `schema`: the string `cbc/1`.
- `w0_root`, `w1_root`: weight roots of the host before and after the change.
- `claim`: the behaviour claim defined below.
- `probe_spec`: how admission probes are derived after commitment.
- `search_spec`: the dispute search budget and method.
- `id`: SHA-256 of the canonical encoding of all fields above.

Signatures, pricing, lineage with several parents, and the state cell are in the proposal. They are not in v1. V1 exists to run Experiment B: can a claim plus a one-input dispute catch what probe admission missed?

V0 used a cube domain, every coordinate in [-6, 6]. The pilot killed it: at cube corners both models extrapolate and even benign grafts change by 7 to 11 RMS, against 21 to 95 for trigger grafts. V1 therefore claims over a distribution ellipsoid, defined below. The pilot outputs are kept in this folder (`pilot-max.json` is the cube reading, `pilot-ellipsoid.json` the ellipsoid reading).

## Weight root

For each named tensor, the leaf hash is SHA-256 over a domain string, a canonical JSON header (name, shape, dtype), and the tensor bytes in C order, little-endian. The root is SHA-256 over the domain string and the leaf hashes in sorted name order.

Two tensors with the same bytes and different shapes hash differently. Two dicts with the same tensors in different insertion order root identically. This fixes the headerless `tobytes()` hash in the Plasm cycle.

## The claim (native retention, ellipsoid form)

The claim covers one predicate only:

For every input `x` in the stated domain, `change(x) <= tau`, where `change(x)` is the root-mean-square over outputs of `f1(x) - f0(x)`, `f0` is the host at `w0_root`, and `f1` is the host at `w1_root`.

The domain for the E13 harness is fixed as follows. Inputs have 24 columns: 16 data columns, 5 gate columns (16 to 20), and 3 nuisance columns (21 to 23).

The 19 non-gate columns are standardized by the shifted native sampler (data columns mean 0.25, sd 1.30. Nuisance columns mean -0.30, sd 0.85). An input is in the domain when every coordinate is finite and within [-8, 8] and the sum of squared standardized non-gate coordinates is at most 64.

The largest gate column must also be a native skill (0 or 1), with value at least 1.5.

The ellipsoid keeps single-coordinate excursions in the claim. One coordinate can reach 8 sd when the rest sit near their means. Multi-coordinate corners stay out.

The admission record's trigger, nuisance column 23 at 4.0 to 4.5, is 5.1 to 5.6 sd. It stays inside the claimed domain on typical rows. Novel-skill behaviour is not part of this claim. It is measured separately as ground truth, as in the admission record.

`tau` is written as a decimal string and parsed as an exact fraction for comparison reporting. The forward passes themselves run in float64 NumPy. That is the v1 arithmetic. Cross-host bit equality is Experiment A and is not claimed here.

Outside the ellipsoid the claim says nothing. A deployed system would need a domain guard or quiet-by-construction there. V1 has neither, and the record must not read as if it does.

## Probe order

The candidate is committed first: `w1_root` and the claim id exist before any admission probe is drawn. Probe inputs are then derived from a seed computed as SHA-256 over the domain string, the test-set identifier, `w1_root` and the claim id. Changing one weight changes the probes. A proposer cannot fit probes they have not seen.

An evaluator cannot pick probes after seeing the candidate without changing the derivation. This is the order Proposition 2 of the calibration theory requires.

## Dispute

A dispute is one input `x`. The verifier checks domain membership, recomputes both forward passes, and the claim falls when `change(x) > tau`. No other evidence is needed. A dispute input outside the domain refutes nothing and is reported as such.

Admission in v0 is the search for a dispute input, run by the host before accepting:

1. Draw fresh native base rows using the probe derivation.
2. Coordinate sweep: for each non-gate column, set that column to each value on a fixed grid in standardized units, holding the rest of the base row fixed.
3. Random search: sample standardized perturbations of base rows.
4. Hill climb: from the best candidates found, take coordinate steps that increase `change(x)`.

Every candidate row is projected into the ellipsoid before it is evaluated, so the search can only produce witnesses the verifier will accept as in-domain.

The budget is counted in evaluated rows and is part of `search_spec`. If the search finds a refutation, the change is rejected and the input is kept as the reason. If it does not, the change is admitted under a sampled reading only: no counter-example found within budget. The record must say which.

## What v1 does not do

No signatures and no registry. No pricing. No novel-skill claim. No guarantee outside the ellipsoid, and no domain guard. No claim that bounded search finds every trigger: measuring that gap is the experiment. Admission by bounded search is a sampled reading. A later dispute with more compute can still refute an admitted change, and that is by design.

## Disclosure

Written by an AI agent session with human oversight.
