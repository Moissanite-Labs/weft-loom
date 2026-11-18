# C11 Triangular Sum anchors under a two-tiered gate

## Question

Does the two-tiered anchor gate in spliceware keep a champion that passes all four Triangular Sum anchors, when a fuel-only tournament on the same candidates settles on the zero-fuel collapse? And once the gate is wired into the real substrate, does the same split appear over generations rather than over five fixed byte strings?

## Status

`design`

The harness runs today and its output is recorded below. It measures the gate rule, which is arithmetic. It measures nothing about search, and the second question above has not been run.

## Preregistration

Not preregistered. Nothing here is a confirmatory result. The predictions for a run against the real substrate are listed under "What a run against the substrate would test" and would be written into a preregistration file before any such run.

## What the harness does

`harness.c` re-declares the four anchors and the gate rule from the spliceware corpus at commit `c1329b2`. It includes nothing from that repository and does not link to it. Five byte strings stand in for candidate genotypes:

| Genotype | First byte | Behaviour | Fuel |
|---|---|---|---|
| `HALT 0x00` | `0x00` | Emits 0 for every input. Burns no fuel. | 0 |
| `IDENT` | `0x01` | Returns the input. | 1 per run |
| `ADD8 unroll` | `0x02` | Fixed eight-step add chain, straight line. | 8 per run |
| `TRI loop` | `0x03` | Iterative `n(n+1)/2 mod 256`. | `2 + 2n` per run |
| `TRI loop, wrong at 37` | `0x04` | Same loop, returns 189 at `n = 37`. | `1 + 2n` per run |

Each string is scored against the four anchors `(0, 0)`, `(5, 15)`, `(13, 91)`, `(37, 191)`. A run that spends more than 512 steps fails its anchor, which is the substrate's fuel cap. The harness then runs two comparisons over the same scores:

- A fuel-only tournament, where the cheaper cell wins and nothing else counts. This is the rule the corpus says collapses.
- The two-tier gate. Tier 1 promotes on a strict 4 of 4 anchors, comparing anchor count first and fuel second, so a cheaper near miss cannot take the crown. Tier 2 admits 3 of 4 into a donor pool.

The seed for the gate is the `HALT` genotype, so the collapse has to be displaced rather than assumed away.

## How to rerun

From this folder, with any C11 compiler:

```
gcc -O3 -Wall -Wextra -std=c11 harness.c -o harness
./harness
```

The harness exits 0 when every decision matches the expectation it prints. Run on macOS 27.0.1, arm64, with two compilers: Apple clang 21.0.0 (reported as `gcc`) and Homebrew GCC 16.2.0. Both compiled with no warnings under `-O3 -Wall -Wextra -std=c11`, and both produced the output below, byte for byte.

## Output

```
anchors: (0,0) (5,15) (13,91) (37,191)

genotype                    anchors   err  fuel
HALT 0x00 (collapse)           1/4   297     0
IDENT                          1/4   242     4
ADD8 unroll                    0/4   226    32
TRI loop                       4/4     0   118
TRI loop, wrong at 37          3/4     2   114

fuel-only tournament champion: HALT 0x00 (collapse) (anchors 1/4, fuel 0)
  expected HALT 0x00 (collapse): ok

two-tier gate, seed = HALT 0x00 (collapse)
  discard  IDENT                  (anchors 1/4, fuel 4)
  discard  ADD8 unroll            (anchors 0/4, fuel 32)
  promote  TRI loop               (anchors 4/4, fuel 118)
  pool     TRI loop, wrong at 37  (anchors 3/4, fuel 114)

two-tier champion: TRI loop (anchors 4/4, fuel 118)
  expected TRI loop: ok
pool donor: TRI loop, wrong at 37 (anchors 3/4, fuel 114)
  expected TRI loop, wrong at 37: ok

all decisions as expected
```

Two things in that output are worth reading closely, and neither is a surprise in a toy this small. The fuel-only rule picks the cell that does nothing, because zero cost cannot be beaten. The two-tier gate picks the 4/4 cell and keeps the 3/4 cell that costs four steps less, even though it is cheaper, because anchor count is compared before cost.

## What a run against the substrate would test

The harness stops at arithmetic. The next step is a copy of [`v3_evogenesis.c`](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/substrates/c11/v3_evogenesis.c) with a switch that selects the comparison rule, driven over a fixed seed list.

The same patch applies to [`v4_unigenesis.c`](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/substrates/c11/v4_unigenesis.c), whose header carries the anchors at word indices 14 and 15.

The lineage of the two files is in the [C11 changelog](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/substrates/c11/CHANGELOG.md), and the gate is specified in the [proposals document](https://github.com/Moissanite-Labs/spliceware/blob/c1329b2471c81087e36ff11c15309d6b28a8247e/docs/proposals/2026-11-lexicase-and-triangular-sum.md).

Predictions, to be recorded before the run and not counted as results here:

| | Prediction |
|---|---|
| P1 | With the two-tier gate, the champion passes 4 of 4 anchors for the whole run on every seed. |
| P2 | With the fuel-only comparison, the champion reaches `0x00` HALT within the first few hundred generations on every seed. |
| P3 | With a strict 4/4 gate and no pool, the run stalls below 4 of 4 for its whole length on most seeds. |

P3 is the half that matters most for weft. If a strict gate alone stalls, then the pool is doing the work, and copying only the 4 of 4 rule would import the cliff without the ladder.

## Limits

- Five fixed byte strings with one opcode each. No stack, no memory, no crossover, no mutation, no arena, no UDP. The harness shows the gate rule and nothing about evolution.
- The evaluator is a stub. Outputs and fuel counts were written by hand to make the four anchor outcomes appear. They are not produced by the C11 VM.
- The gate tiebreak differs from `v3_evogenesis.c`, which breaks an anchor tie on total anchor error before anything else. The harness breaks it on fuel, following the proposal's "better fuel margin", then on error. A run wired into the substrate would use the code's order.
- Anchors are 8-bit and comparison is modulo 256. A probe set on weight cells would need wider values and a tolerance.
- The harness does not model weft's budget precondition, which requires a strictly positive cost. The collapse cell is the seed, so the question is whether a zero-cost cell ever loses a tournament, not whether weft would admit one.
- Nothing here touches a real model or a checkpoint. The link to weft is an argument from the gate, not a measurement on weights.
- One machine, two compilers, one run each. No second host was tried.

## Disclosure

Written and run by an agent session on 2026-11-18, from the spliceware corpus captured by mithrax-exo in November 2026. The source material keeps its original author and date. The gate rule tested here is the corpus's, not this session's.
