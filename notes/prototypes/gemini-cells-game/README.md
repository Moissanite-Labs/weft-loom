# Gemini cells game

A small exact game-theory model of two twin agents ("cells") that take turns.
A cell cannot change itself. It can only improve its twin's harness.
The model checks claims about which scoring rules give a cell a reason to
build up its twin's builder capability.

Everything is exact integer or `fractions.Fraction` arithmetic.
There is no randomness and no outside call. Python standard library only.

## The model

There are two cells, A and B.
Each cell has a harness with two numbers.

- `f` is the task capability. It is what a benchmark measures.
- `c` is the builder capability. It is how much the cell can do for its twin per turn.

The state is `(fA, cA, fB, cB)`. All four start at 0.
The game lasts `T` turns. `T` is even. A moves on odd turns, B on even turns.

On its turn the mover has `e = 1 + c` effort units, where `c` is its own builder capability.
Each unit goes to the twin's harness in one of two ways.

- A narrow unit adds 2 to the twin's `f`.
- A general unit adds 1 to the twin's `c` and adds `G` to the twin's `f`.

The twin's `c` cannot go above `Cmax`.
So a move is a number `k` of general units with `0 <= k <= min(e, Cmax - c_twin)`.
The other `e - k` units are narrow.

`G` is 0, 1, 2 or 3.
`G = 0` is a pure builder tool.
`G = 2` makes a general unit worth as much on the benchmark as a narrow unit.
`f` is counted in half-units so that all numbers stay integers.

Sabotage is optional. With `S = 1` the mover may also lower the twin's `c` by 1.
This costs no effort. It is applied before the general units of the same move.
A move is then a pair `(sab, k)`.

## Scoring regimes

| Regime | What the mover maximises |
|---|---|
| `CROSS` | A gets `fB` at the end. B gets `fA` at the end. |
| `RIVAL` | A gets `fB - fA` at the end. B gets the negative of that. Zero-sum. |
| `COLLECTIVE` | Both get `fA + fB` at the end. |
| `GREEDY` | The twin's `f` right after its own move. No lookahead. |
| `ROUNDTRIP(gamma)` | Own gain in the twin's `f`, plus `gamma` times the gain in its own `f` from the twin's next move. The twin's next move is assumed to be its GREEDY move. `gamma` is 0, 0.5, 1 or 2. On the last turn this is GREEDY. |
| `CROSS_SUM`, `RIVAL_SUM`, `COLLECTIVE_SUM` | As the first three, but the payoff is summed over the state after every turn 1..T. |

## Solution concept and tie rules

`CROSS`, `RIVAL`, `COLLECTIVE` and the `_SUM` variants are solved for a
subgame-perfect equilibrium by backward induction over the full game tree.
`GREEDY` and `ROUNDTRIP` are fixed rules. They are simulated forward.

A mover that is indifferent uses a tie rule. Both are run for every case.

- `min_general`: fewest general units, then no sabotage.
- `max_general`: most general units, then no sabotage.

A claim counts as holding only if it holds under both tie rules.

## Grid

- `T` in {2, 4, 6, 8, 10, 12}
- `Cmax` in {1, 2, 3}
- `G` in {0, 1, 2, 3}
- `S` in {0, 1}
- 11 regimes
- 2 tie rules

That is 3168 cases. All are solved. None were dropped.

## Assumptions

- There are exactly two players. Each knows all parameters and the whole history.
- `T` is even. A moves first. B moves last.
- All state numbers are integers and start at 0.
- A mover cannot change its own harness.
- Effort on a turn is 1 plus the mover's own `c` at the start of that turn.
- Every effort unit must be spent. A unit is narrow or general. There is no third use.
- A narrow unit is always worth 2. A general unit is always worth `G`. These values do not change over time.
- One unit of `c` gives one more effort unit on every later turn of its owner. It has no other effect.
- `c` does not decay. `f` never goes down.
- `c` cannot exceed `Cmax`.
- Sabotage is free. At most one sabotage per turn. It lowers the twin's `c` by exactly 1. It does not lower `f`.
- There is no discounting, no noise and no hidden move.
- In the equilibrium regimes both players are fully rational and far-sighted, and both know it.
- In `ROUNDTRIP` the mover assumes a greedy twin. The real twin follows `ROUNDTRIP` too.
- The same tie rule is used by both players at every node, on and off the path.
- Efficiency is always measured on `fA + fB` at the end, also for the `_SUM` regimes.
- The first-best excludes sabotage.

## Choices made where the spec left room

- Sabotage when the twin's `c` is 0 would change nothing. It is not offered as a move.
- The cap is checked after the sabotage: `0 <= k <= min(e, Cmax - (c_twin - sab))`. So a sabotage frees room for one more general unit in the same move.
- The other reading (room counted before the sabotage) is run as a supplement only. It is `S = 2` in the code.
- With `max_general`, an indifferent mover may sabotage if that lets it place more general units. This follows from "most general units, then no sabotage".
- In `ROUNDTRIP` with `S = 1` the twin's assumed greedy move may include a sabotage. Only its gain in `f` is used, so the tie rule of that assumed move does not matter.
- "General investment" of a case means general units placed on the path. It is not the value of `c` at the end.
- "Sabotage whenever the twin's c is positive" (C1) is checked two ways: on the equilibrium path, and at every decision node, reachable or not.
- "Concentrated in the early turns" (C4) is turned into two statements: the investing turns are turns 1..s with no gap, and s is at most T/2.
- "Zero in the final turns" (C4) is turned into: `k = 0` on the last turn.
- The equilibrium paths come from the solver that memoises on `(t, fA, cA, fB, cB)`, as specified. A second solver that memoises on `(t, cA, cB)` is used as a cross-check.

## Files

- `game.py`: the model, both solvers, the grid run and the report.
- `game.out`: the exact stdout of `python3 game.py`.
- `game_cases.json`: one row per solved case. Parameters, path, end state, efficiency. One row per line. It is 2.7 MB and is not committed: `game.py` rewrites it. The file the checks here were run against has SHA-256 `158ad741cace1b36953a2d03dec3aed8503b30fa76d3c2414aa0a269c51b347d`.
- `test_game.py`: the unit tests.
- `test_game.out`: the output of the unit tests.
- `recheck.py`: a second solver, written by the lead of the session without reading `game.py`. It re-solves every case in `game_cases.json` and compares the end state and every move.
- `recheck.out`: its output. 3168 cases, 0 mismatches.
- `README.md`: this file.

## How to rerun

```
python3 game.py > game.out
python3 -m unittest -v test_game > test_game.out 2>&1
python3 recheck.py > recheck.out
```

`game.py` also rewrites `game_cases.json`.
It prints its timing to stderr, so stdout is the same on every run.
On the machine used here (Python 3.13) `game.py` took about 50 seconds:
about 26 for the grid with its cross-check, about 23 for the two supplements, under 1 for the report.
The tests took about 7 seconds and `recheck.py` about 13.

## What is in game.out

- Section 0: self-checks made during the run.
- Section 1: the first-best table, the cases with efficiency above 1, sabotage on the path.
- Section 2: where the two tie rules give different paths.
- Section 3: claims C1 to C8. Each sub-claim has a statement, a count, the exact list of exceptions and a verdict.
- Supplement U: `COLLECTIVE` and `CROSS` with a cap that never binds. Outside the requested grid.
- Supplement V: the other reading of the sabotage rule. Outside the requested grid.
- Section 4: one line per sub-claim.
- Appendix A: one line per case.

Exceptions are written as boxes. `G=2, tie=max_general [36]` means all 36 cases
of the domain with those values, for every value of the parameters not named.

## What the tests check

- Hand-derived cases, with the derivation in comments. `T = 2`, `Cmax = 1`, `G = 0` for `CROSS`, `RIVAL` and `COLLECTIVE`, and eight more test methods.
- The rules in `game.py` against a separate reference implementation in the test file.
- Subgame perfection, checked directly. For `T <= 4` and `Cmax <= 2`, at every turn and every state, no single-move deviation by the mover improves its continuation payoff. The states are all reachable ones plus a grid of unreachable ones. Both solvers are checked.
- The first-best from a separate plain exhaustive search equals the `COLLECTIVE` equilibrium value. This is done for every `(T, Cmax, G)` of the grid, not only `T <= 8`.
- `RIVAL` and `RIVAL_SUM` payoffs sum to zero at every node.
- The two solvers give the same path and value.
- `ROUNDTRIP(0)` equals `GREEDY`.
- The exception lists in the report are exact.
- `game_cases.json` matches a fresh solve.

## Claim verdicts

Verdict words.
"Follows": the statement holds in every case of its domain.
"Fails": it holds in no case.
"Depends on X": it holds in some cases, and X are the parameters needed to say which.
"Vacuous": the domain is empty.
A case includes its tie rule. So "depends on tie" means the statement does not
hold under both tie rules.
Counts are cases unless another unit is named.
`cap_binds` means the mover has more effort units than free cap room in the twin, before any sabotage.

| ID | Statement | Holds | Verdict | Exceptions |
|---|---|---|---|---|
| C1.a | `RIVAL`, G in {0,1}: total general investment = 0 | 144 of 144 | Follows | none |
| C1.b | `RIVAL`, G = 2: total general investment = 0 | 36 of 72 | Depends on tie | tie=max_general [36] |
| C1.c | `RIVAL`, G = 3: total general investment = 0 | 0 of 72 | Fails | all 72. In each, B places 1 general unit on turn T |
| C1.d | `RIVAL`, every G: k = 0 on every turn before the last | 288 of 288 | Follows | none |
| C1.e | `RIVAL`, S = 1, on the path: every turn that starts with twin c > 0 has sab = 1 | 0 of 0 turns | Vacuous | no such turn on any path |
| C1.f | `RIVAL`, S = 1, every decision node with twin c > 0, reachable or not: sab = 1 | 6048 of 6720 nodes | Depends on last turn, G, tie, cap_binds | last turn and cap_binds=no [192]; last turn, cap_binds=yes, G in {0,1} [384]; last turn, cap_binds=yes, G=2, tie=min_general [96] |
| C1.g | As C1.f, nodes before the last turn only | 5760 of 5760 nodes | Follows | none |
| C1.h | `RIVAL`, G in {0,1}: k = 0 at every decision node, reachable or not | 9744 of 9744 nodes | Follows | none |
| C2.a | `GREEDY`, G in {0,1}: total general investment = 0 | 144 of 144 | Follows | none |
| C2.b | `GREEDY`, G = 2: total general investment = 0 | 36 of 72 | Depends on tie | tie=max_general [36]. Every legal move ties at G = 2 |
| C2.c | `GREEDY`, G = 3: total general investment > 0 | 72 of 72 | Follows | none |
| C2.d | `GREEDY`: investment = 0 exactly when G < 2 | 252 of 288 | Depends on G, tie | G=2, tie=min_general [36] |
| C3.a | `CROSS`, G in {0,1}: total general investment = 0, every T | 144 of 144 | Follows | none |
| C3.b | `CROSS`, G = 2: total general investment = 0 | 36 of 72 | Depends on tie | tie=max_general [36] |
| C3.c | `CROSS`, G = 3: total general investment = 0 | 0 of 72 | Fails | all 72 |
| C3.d | `CROSS`, G in {0,1}: k = 0 at every decision node, reachable or not | 9744 of 9744 nodes | Follows | none |
| C4.a | `COLLECTIVE`: total general investment > 0 | 282 of 288 | Depends on T, G, tie | T=2, G=0, tie=min_general [6] |
| C4.b | `COLLECTIVE`: investment at some T implies investment at every larger T of the grid | 48 of 48 configurations | Follows | none |
| C4.c | `COLLECTIVE`, cases with investment: investing turns are 1..s with no gap | 282 of 282 | Follows | none |
| C4.d | `COLLECTIVE`: k = 0 on the last turn | 222 of 288 | Depends on T, Cmax, G, S, tie | G=2, S=0, T=2, max_general [3]; G=2, S=0, T=4, Cmax=3, max_general [1]; G=2, S=1, max_general [18]; G=3, S=0, T=2 [6]; G=3, S=0, T=4, Cmax=3 [2]; G=3, S=1 [36] |
| C4.e | `COLLECTIVE`: build-then-harvest (C4.a and C4.c and C4.d together) | 216 of 288 | Depends on T, Cmax, G, S, tie | the 66 of C4.d plus G=0, T=2, min_general [6] |
| C4.f | `COLLECTIVE`, cases with investment: last investing turn is at most T/2 | 186 of 282 | Depends on T, Cmax, G, S, tie | 96 cases, listed in `game.out` |
| C4.g | `COLLECTIVE`, cases with investment: both c end at the cap | 230 of 282 | Depends on T, Cmax, G, tie | 52 cases, all with T <= 6, listed in `game.out` |
| C4.h | `COLLECTIVE`, S = 0, T < 12: switch turn equals the switch turn at T = 12 | 91 of 120 | Depends on T, Cmax, G, tie | 29 cases, all with T <= 6, listed in `game.out` |
| C4.i | `COLLECTIVE`, G in {0,1}: build-then-harvest as in C4.e | 138 of 144 | Depends on T, G, tie | T=2, G=0, tie=min_general [6] |
| C5.threshold | `ROUNDTRIP`: investment occurs exactly when G + 2*gamma > 2, or G + 2*gamma = 2 and tie=max_general | 1152 of 1152 | Follows | none |
| C5.efficient | `ROUNDTRIP`, cases with investment: end score = `COLLECTIVE` end score | 828 of 828 | Follows | none |
| C6.a | S = 0: `COLLECTIVE` end score >= end score of every other regime | 1584 of 1584 | Follows | none |
| C6.b | S = 0, G in {0,1}: `COLLECTIVE` end score > `CROSS` end score | 66 of 72 | Depends on T, G | T=2, G=0 [6] (equal scores) |
| C7.a | `COLLECTIVE`: the twins end equal (fA = fB and cA = cB) | 6 of 288 | Depends on T, G, tie | T=2, G=0, max_general [6]; T=2, G in {1,2,3} [36]; T >= 4 [240] |
| C7.b | `COLLECTIVE`, cases with fA != fB: fA > fB | 282 of 282 | Follows | none |
| C7.c | `COLLECTIVE`, cases with cA != cB: cB > cA | 40 of 52 | Depends on T, Cmax, G, tie | G=2, T=2, Cmax in {2,3}, max_general [4]; G=3 [8] |

C5, per cell: does `ROUNDTRIP(gamma)` invest? Each cell covers 72 cases.

| gamma | G = 0 | G = 1 | G = 2 | G = 3 |
|---|---|---|---|---|
| 0 | never | never | max_general only | always |
| 0.5 | never | max_general only | always | always |
| 1 | max_general only | always | always | always |
| 2 | always | always | always | always |

C5, end score divided by the `COLLECTIVE` end score, S = 0, mean over T, Cmax and tie rule.

| gamma | G = 0 | G = 1 | G = 2 | G = 3 |
|---|---|---|---|---|
| 0 | 0.6276 | 0.5273 | 0.7300 | 1.0000 |
| 0.5 | 0.6276 | 0.7637 | 1.0000 | 1.0000 |
| 1 | 0.8138 | 1.0000 | 1.0000 | 1.0000 |
| 2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

C6, mean efficiency per regime, S = 0, 144 cases each.

| Regime | Mean | min_general | max_general | G < 2 only |
|---|---|---|---|---|
| `COLLECTIVE` | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `ROUNDTRIP(2)` | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `COLLECTIVE_SUM` | 0.9885 | 0.9769 | 1.0000 | 0.9769 |
| `ROUNDTRIP(1)` | 0.9535 | 0.9069 | 1.0000 | 0.9069 |
| `ROUNDTRIP(0.5)` | 0.8478 | 0.7887 | 0.9069 | 0.6956 |
| `GREEDY` | 0.7212 | 0.6537 | 0.7887 | 0.5775 |
| `ROUNDTRIP(0)` | 0.7212 | 0.6537 | 0.7887 | 0.5775 |
| `CROSS_SUM` | 0.7212 | 0.6537 | 0.7887 | 0.5775 |
| `CROSS` | 0.6818 | 0.5750 | 0.7887 | 0.5775 |
| `RIVAL_SUM` | 0.5185 | 0.5122 | 0.5249 | 0.5775 |
| `RIVAL` | 0.5122 | 0.5122 | 0.5122 | 0.5775 |

C6, `COLLECTIVE` end score divided by `CROSS` end score, S = 0, G in {0,1}, over Cmax.

| T | Mean | Min | Max |
|---|---|---|---|
| 2 | 1.1250 | 1.0000 | 1.2500 |
| 4 | 1.4792 | 1.2500 | 1.8750 |
| 6 | 1.9444 | 1.5000 | 2.5000 |
| 8 | 2.2083 | 1.6250 | 2.8750 |
| 10 | 2.3667 | 1.7000 | 3.1000 |
| 12 | 2.4722 | 1.7500 | 3.2500 |

C8, the sub-claims of C1, C3 and C4 evaluated again with the `_SUM` regimes.
C2 has no summed variant.

| Sub-claim | End scoring | Summed scoring | Change |
|---|---|---|---|
| C1.a, C1.b, C1.c, C1.e, C1.f, C1.g, C1.h | as above | same counts, same exceptions | none |
| C1.d | 288 of 288, follows | 276 of 288, depends on Cmax, G, tie. Exceptions: Cmax=1, G=3, max_general [12] | verdict changes |
| C3.a, C3.b, C3.c, C3.d | as above | same counts, same exceptions | none |
| C4.a | 282 of 288 | 264 of 288. Exceptions: T=2, G=0 [12]; T=2, G=1, min_general [6]; T=4, G=0, min_general [6] | same verdict word, other exceptions |
| C4.b | 48 of 48 | 48 of 48 | none |
| C4.c | 282 of 282 | 264 of 264 | same verdict, smaller domain |
| C4.d | 222 of 288 | 222 of 288, same exceptions | none |
| C4.e | 216 of 288 | 198 of 288 | same verdict word, other exceptions |
| C4.f | 186 of 282 | 178 of 264 | same verdict word, other exceptions |
| C4.g | 230 of 282 | 220 of 264 | same verdict word, other exceptions |
| C4.h | 91 of 120 | 86 of 120 | same verdict word, other exceptions |
| C4.i | 138 of 144 | 120 of 144. Exceptions: T=2, G=0 [12]; T=2, G=1, min_general [6]; T=4, G=0, min_general [6] | same verdict word, other exceptions |

The switch-turn tables, the smallest T with investment, the symmetry counts and
the full exception lists are in `game.out`.

## Limits

- The grid is small: T at most 12 and Cmax at most 3.
- In the grid, with S = 0, the last investing turn under `COLLECTIVE` is never later than turn 4. The grid cannot show what happens when the cap does not bind. Supplement U runs `COLLECTIVE` and `CROSS` with a cap that never binds. It is outside the requested grid.
- Payoffs are linear and all units are integers. This produces many exact ties. Where the report says "depends on tie", the model does not pick an answer.
- Only two tie rules were run. Other rules were not.
- Where ties exist there are other subgame-perfect equilibria. They are not enumerated. Each case reports the one equilibrium selected by its tie rule.
- The model has perfect information, no noise and no learning. Each cell knows G, Cmax, T and the other cell's objective.
- The horizon is finite and known. There is no repeated-game or reputation effect beyond the T turns.
- A unit of builder capability always gives exactly one more effort unit per turn. There are no decreasing or increasing returns and no decay.
- A narrow unit is always worth 2 and a general unit always G. The benchmark value of tools does not change over time.
- `GREEDY` and `ROUNDTRIP` are fixed rules. They are not equilibria. `ROUNDTRIP` assumes a greedy twin, which is not what the twin does.
- Sabotage is free and limited to one unit per turn. The sabotage results depend on the reading of the rule. Supplement V shows the other reading.
- Efficiency is measured against a first-best without sabotage. With S = 1 it can be above 1.
- Efficiency uses the end state for every regime. For the `_SUM` regimes this is not what the players maximise.
- The claims were given in words. The precise statements used here are one possible reading of them. They are written out in `game.out`.
- The equilibrium paths of the grid were computed by two independent memoisations and agree. Supplements U and V use the reduced solver only; the tests compare it with the literal solver for T at most 6 there.
- The tests check subgame perfection directly only for T at most 4 and Cmax at most 2.
