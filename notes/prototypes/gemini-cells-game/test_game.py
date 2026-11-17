#!/usr/bin/env python3
"""Tests for game.py.

Run:  python3 -m unittest -v test_game

The tests use their own small reference implementation of the rules
(`ref_moves`, `ref_step`, `ref_payoff`).  It is written separately from
game.py on purpose, so that a mistake in game.legal_moves / game.apply_move /
game.payoff would show up as a disagreement.
"""

import json
import os
import unittest
from fractions import Fraction

import game

START = (0, 0, 0, 0)


# ----------------------------------------------------------------------------
# Independent reference implementation of the rules
# ----------------------------------------------------------------------------

def ref_moves(t, state, Cmax, S):
    """All legal (sab, k) for the mover of turn t."""
    _fA, cA, _fB, cB = state
    own, twin = (cA, cB) if t % 2 == 1 else (cB, cA)
    effort = 1 + own
    moves = []
    for sab in (0, 1):
        if sab == 1 and (S == 0 or twin == 0):
            continue
        # S = 1 (the model): the cap is checked after the sabotage.
        # S = 2 (supplement only): the cap room is counted before it.
        twin_c = twin - sab if S == 1 else twin
        k = 0
        while k <= effort and twin_c + k <= Cmax:
            moves.append((sab, k))
            k += 1
    return moves


def ref_step(t, state, move, G):
    fA, cA, fB, cB = state
    sab, k = move
    if t % 2 == 1:                      # A improves B
        narrow = (1 + cA) - k
        return (fA, cA, fB + 2 * narrow + G * k, cB - sab + k)
    narrow = (1 + cB) - k               # B improves A
    return (fA + 2 * narrow + G * k, cA - sab + k, fB, cB)


def ref_payoff(base, state):
    fA, _, fB, _ = state
    if base == "CROSS":
        return (fB, fA)
    if base == "RIVAL":
        return (fB - fA, -(fB - fA))
    if base == "COLLECTIVE":
        return (fA + fB, fA + fB)
    raise ValueError(base)


def ref_tie_order(move, tie):
    sab, k = move
    return (k, sab) if tie == "min_general" else (-k, sab)


def rollout(policy, T, G, t, state, first_move, base, summed):
    """Play `first_move` at turn t, then follow `policy` to the end.
    Returns the continuation payoffs (uA, uB) counted from turn t on."""
    s = ref_step(t, state, first_move, G)
    states = [s]
    for u in range(t + 1, T + 1):
        s = ref_step(u, s, policy(u, s), G)
        states.append(s)
    if not summed:
        return ref_payoff(base, states[-1])
    uA = sum(ref_payoff(base, x)[0] for x in states)
    uB = sum(ref_payoff(base, x)[1] for x in states)
    return (uA, uB)


def reachable_states(T, Cmax, G, S):
    """{t: set of states that some move sequence reaches at the start of t}."""
    layers = {1: {START}}
    for t in range(1, T):
        nxt = set()
        for s in layers[t]:
            for m in ref_moves(t, s, Cmax, S):
                nxt.add(ref_step(t, s, m, G))
        layers[t + 1] = nxt
    return layers


def exhaustive_best_total(T, Cmax, G, S):
    """max of fA + fB at the end over every move sequence.  Plain depth-first
    enumeration of whole sequences.  No memo, no solver, reference rules."""
    best = -1
    stack = [(1, START)]
    while stack:
        t, s = stack.pop()
        if t > T:
            best = max(best, s[0] + s[2])
            continue
        for m in ref_moves(t, s, Cmax, S):
            stack.append((t + 1, ref_step(t, s, m, G)))
    return best


def solve(T, Cmax, G, S, regime, tie, literal=True):
    player = game.make_player(T, Cmax, G, S, regime, tie, literal=literal)
    path, states = game.play(player)
    return player, [(sab, k) for (_, _, sab, k, _) in path], states[-1]


# ----------------------------------------------------------------------------
# (a) hand-derived cases
# ----------------------------------------------------------------------------

class HandDerived(unittest.TestCase):
    """Each case is derived by hand in the comment, then asserted for the
    literal solver and for the reduced solver."""

    def check(self, T, Cmax, G, S, regime, tie, moves, end, value=None):
        for literal in (True, False):
            player, got_moves, got_end = solve(T, Cmax, G, S, regime, tie,
                                               literal)
            self.assertEqual(got_moves, moves, (regime, tie, literal))
            self.assertEqual(got_end, end, (regime, tie, literal))
            if value is not None:
                self.assertEqual(player.value(1, START), value)

    # The tree for T = 2, Cmax = 1, G = 0, S = 0 (used by the next 3 tests).
    #
    # Turn 1, A has e = 1 + cA = 1 unit:
    #   k = 0 (narrow):   fB = 2, cB = 0          state (0,0,2,0)
    #   k = 1 (general):  fB = 0, cB = 1          state (0,0,0,1)
    # Turn 2, B has e = 1 + cB units:
    #   after A's k = 0 (e = 1):  k = 0 -> fA = 2        k = 1 -> fA = 0, cA = 1
    #   after A's k = 1 (e = 2):  k = 0 -> fA = 4        k = 1 -> fA = 2, cA = 1
    #                             (cap 1, so at most one general unit)

    def test_T2_cross(self):
        # CROSS: uA = fB_end, uB = fA_end.
        # B (turn 2) wants fA large: k = 0 in both subgames (2 > 0, 4 > 2).
        # A (turn 1): k = 0 gives uA = fB = 2; k = 1 gives uA = fB = 0.
        # So A plays k = 0.  No tie anywhere.  End (2,0,2,0), payoffs (2,2).
        for tie in game.TIE_RULES:
            self.check(2, 1, 0, 0, "CROSS", tie, [(0, 0), (0, 0)],
                       (2, 0, 2, 0), (2, 2))

    def test_T2_rival(self):
        # RIVAL: uA = fB_end - fA_end, uB = -uA.
        # B (turn 2) cannot change fB, so it maximises fA: k = 0 both times.
        # A: k = 0 gives fB - fA = 2 - 2 = 0; k = 1 gives 0 - 4 = -4.
        # So A plays k = 0.  No tie.  End (2,0,2,0), payoffs (0,0).
        for tie in game.TIE_RULES:
            self.check(2, 1, 0, 0, "RIVAL", tie, [(0, 0), (0, 0)],
                       (2, 0, 2, 0), (0, 0))

    def test_T2_collective(self):
        # COLLECTIVE: uA = uB = fA_end + fB_end.
        # B (turn 2): k = 0 in both subgames (totals 2+2 > 0+2 and 4+0 > 2+0).
        # A: k = 0 gives 2 + 2 = 4; k = 1 gives 0 + 4 = 4.  A TIE.
        # min_general -> k = 0, end (2,0,2,0).
        # max_general -> k = 1, end (4,0,0,1).  The value is 4 either way.
        self.check(2, 1, 0, 0, "COLLECTIVE", "min_general",
                   [(0, 0), (0, 0)], (2, 0, 2, 0), (4, 4))
        self.check(2, 1, 0, 0, "COLLECTIVE", "max_general",
                   [(0, 1), (0, 0)], (4, 0, 0, 1), (4, 4))

    def test_T2_collective_G1(self):
        # Same tree with G = 1: a general unit adds 1 to f.
        # A k = 0: fB = 2; B (e = 1): k = 0 -> fA = 2 (total 4),
        #                              k = 1 -> fA = 1 (total 3).   -> 4
        # A k = 1: fB = 1, cB = 1; B (e = 2): k = 0 -> fA = 4 (total 5),
        #                              k = 1 -> fA = 1 + 2 = 3 (total 4). -> 5
        # 5 > 4, so A invests.  No tie.  End (4,0,1,1), value 5.
        for tie in game.TIE_RULES:
            self.check(2, 1, 1, 0, "COLLECTIVE", tie, [(0, 1), (0, 0)],
                       (4, 0, 1, 1), (5, 5))

    def test_T2_G3_cross_and_rival(self):
        # G = 3: a general unit adds 3 to f, more than a narrow unit.
        # B (turn 2) maximises fA in CROSS and in RIVAL:
        #   after A's k = 0 (e = 1): k = 1 -> fA = 3 (> 2).
        #   after A's k = 1 (e = 2): k = 1 -> fA = 3 + 2 = 5 (> 4).
        # CROSS, A maximises fB: k = 1 gives 3 > 2.  End (5,1,3,1).
        # RIVAL, A maximises fB - fA: k = 0 gives 2 - 3 = -1,
        #                             k = 1 gives 3 - 5 = -2.  So k = 0.
        #   End (3,1,2,0), payoffs (-1, 1).
        for tie in game.TIE_RULES:
            self.check(2, 1, 3, 0, "CROSS", tie, [(0, 1), (0, 1)],
                       (5, 1, 3, 1), (3, 5))
            self.check(2, 1, 3, 0, "RIVAL", tie, [(0, 0), (0, 1)],
                       (3, 1, 2, 0), (-1, 1))

    def test_T4_collective_G0(self):
        # T = 4, Cmax = 1, G = 0, COLLECTIVE.  Totals fA + fB at the end.
        # (a) A invests on turn 1: state (0,0,0,1).  B has e = 2 on turn 2.
        #   B k = 0: (4,0,0,1). Turn 3, A e = 1, cB at cap: fB = 2.
        #            Turn 4, B e = 2: k = 0 -> fA = 8, total 10
        #                             (k = 1 -> fA = 6, total 8).      -> 10
        #   B k = 1: (2,1,0,1). Turn 3, A e = 2, cB at cap: fB = 4.
        #            Turn 4, B e = 2, cA at cap: fA = 2 + 4 = 6.       -> 10
        #   B is TIED on turn 2 (10 = 10).
        # (b) A plays narrow on turn 1: state (0,0,2,0).  B has e = 1.
        #   B k = 0: (2,0,2,0). A k = 0: fB = 4, then B: fA = 4.       ->  8
        #                       A k = 1: fB = 2, cB = 1, B e = 2:
        #                                fA = 2 + 4 = 6.               ->  8
        #   B k = 1: (0,1,2,0). A e = 2: k = 0 -> fB = 6, B: fA = 2.   ->  8
        #                       k = 1 -> fB = 4, cB = 1, B e = 2,
        #                                cA at cap: fA = 4.            ->  8
        # So A invests on turn 1 (10 > 8, strict) and the value is 10.
        # min_general: B plays k = 0 on turn 2.  Path 1,0,0,0, end (8,0,2,1).
        # max_general: B plays k = 1 on turn 2.  Path 1,1,0,0, end (6,1,4,1).
        self.check(4, 1, 0, 0, "COLLECTIVE", "min_general",
                   [(0, 1), (0, 0), (0, 0), (0, 0)], (8, 0, 2, 1), (10, 10))
        self.check(4, 1, 0, 0, "COLLECTIVE", "max_general",
                   [(0, 1), (0, 1), (0, 0), (0, 0)], (6, 1, 4, 1), (10, 10))
        self.assertEqual(game.first_best(4, 1, 0), 10)

    def test_T4_cross_G3_timing_tie(self):
        # T = 4, Cmax = 1, G = 3, CROSS.  Each twin can receive ONE general
        # unit in total (cap 1).  It is worth 3 instead of 2: a bonus of 1.
        # Turn 4, B (maximises fA): gain 2e + 1 if cA = 0, else 2e.
        # Turn 3, A (maximises fB): k = 1 if cB = 0 (bonus 1), strict.
        #   So cB = 1 after turn 3 whatever happened, and B has e = 2 on
        #   turn 4.
        # Turn 2, B: bonus now (k = 1) or bonus on turn 4 (k = 0).  Its
        #   effort on turn 4 is 2 either way.  TIE.
        # Turn 1, A: under min_general B plays k = 0 on turn 2, so A has
        #   e = 1 on turn 3 either way: bonus now or bonus on turn 3.  TIE.
        # min_general: path 0,0,1,1.  fB = 2 + 3 = 5, fA = 2 + (3 + 2) = 7.
        # max_general: path 1,1,0,0.  fB = 3 + 4 = 7, fA = (3 + 2) + 4 = 9.
        self.check(4, 1, 3, 0, "CROSS", "min_general",
                   [(0, 0), (0, 0), (0, 1), (0, 1)], (7, 1, 5, 1), (5, 7))
        self.check(4, 1, 3, 0, "CROSS", "max_general",
                   [(0, 1), (0, 1), (0, 0), (0, 0)], (9, 1, 7, 1), (7, 9))
        self.assertEqual(game.first_best(4, 1, 3), 16)

    def test_sabotage_rival_off_path(self):
        # RIVAL, T = 2, Cmax = 1, G = 0, S = 1.
        # Subgame at turn 1 from the unreachable state (0,0,0,1): cB = 1.
        # A has e = 1 and may sabotage because cB >= 1.
        #   sab = 0: cB stays at the cap, so k = 0: fB = 2.  B has e = 2:
        #            fA = 4.  uA = 2 - 4 = -2.
        #   sab = 1, k = 0: cB = 0, fB = 2.  B has e = 1: fA = 2.  uA = 0.
        #   sab = 1, k = 1: cB = 1, fB = 0.  B has e = 2: fA = 4.  uA = -4.
        # A plays (sab 1, k 0) and gets 0.
        # Subgame at turn 2 from (0,1,0,0): B moves last, cA = 1.
        #   (0,0): fA = 2.   (1,0): fA = 2, cA = 0.   (1,1): fA = 0.
        #   (0,0) and (1,0) tie; both tie rules then take "no sabotage".
        for tie in game.TIE_RULES:
            for literal in (True, False):
                pl = game.make_player(2, 1, 0, 1, "RIVAL", tie, literal)
                self.assertEqual(pl.policy(1, (0, 0, 0, 1)), (1, 0))
                self.assertEqual(pl.value(1, (0, 0, 0, 1)), (0, 0))
                self.assertEqual(pl.policy(2, (0, 1, 0, 0)), (0, 0))
                self.assertEqual(pl.value(2, (0, 1, 0, 0)), (-2, 2))

    def test_summed_T2(self):
        # Summed payoffs, T = 2, Cmax = 1.  The payoff is added up over the
        # state after turn 1 and the state after turn 2.
        # CROSS_SUM, G = 0: A k = 0 gives fB = 2 after both turns: uA = 4;
        #   k = 1 gives uA = 0.  So k = 0.  B: k = 0, fA = 0 then 2: uB = 2.
        # RIVAL_SUM, G = 0: A k = 0: fB - fA = 2 after turn 1 and 2 - 2 = 0
        #   after turn 2: uA = 2.  k = 1: 0 and 0 - 4: uA = -4.  So k = 0.
        # COLLECTIVE_SUM, G = 1:
        #   A k = 0: total 2 after turn 1; B narrow: total 4.   Sum 6.
        #   A k = 1: total 1 after turn 1; B (e = 2) narrow: 5. Sum 6.  TIE.
        #   min_general -> k = 0, end (2,0,2,0); max_general -> k = 1,
        #   end (4,0,1,1).  (With end scoring A invests strictly: 5 > 4.)
        for tie in game.TIE_RULES:
            self.check(2, 1, 0, 0, "CROSS_SUM", tie, [(0, 0), (0, 0)],
                       (2, 0, 2, 0), (4, 2))
            self.check(2, 1, 0, 0, "RIVAL_SUM", tie, [(0, 0), (0, 0)],
                       (2, 0, 2, 0), (2, -2))
        self.check(2, 1, 1, 0, "COLLECTIVE_SUM", "min_general",
                   [(0, 0), (0, 0)], (2, 0, 2, 0), (6, 6))
        self.check(2, 1, 1, 0, "COLLECTIVE_SUM", "max_general",
                   [(0, 1), (0, 0)], (4, 0, 1, 1), (6, 6))

    def test_roundtrip_T2(self):
        # ROUNDTRIP(gamma), T = 2, Cmax = 1, S = 0, turn 1 (A, e = 1), G <= 2.
        #   k = 0: own gain 2.  B then has e = 1: greedy gain 2.
        #          objective 2 + 2 gamma.
        #   k = 1: own gain G.  B then has e = 2: greedy gain 4.
        #          objective G + 4 gamma.
        # General wins iff G + 2 gamma > 2; equal means a tie.
        # Turn 2 is GREEDY: k = 0 when G < 2.
        half = Fraction(1, 2)
        expect = {  # (G, gamma): (objective k=0, objective k=1)
            (0, half): (3, 2), (0, 1): (4, 4), (0, 2): (6, 8),
            (1, half): (3, 3), (1, 1): (4, 5), (1, 0): (2, 1),
        }
        for (G, gamma), (o0, o1) in expect.items():
            rule = game.MyopicRule(2, 1, G, 0, Fraction(gamma), "min_general")
            objs = {move: obj for obj, move, _ in rule.objective(1, START)}
            self.assertEqual(objs, {(0, 0): o0, (0, 1): o1})
            for tie in game.TIE_RULES:
                label = "ROUNDTRIP(%s)" % game.gamma_label(gamma)
                _, moves, _ = solve(2, 1, G, 0, label, tie)
                if o1 > o0 or (o1 == o0 and tie == "max_general"):
                    self.assertEqual(moves, [(0, 1), (0, 0)])
                else:
                    self.assertEqual(moves, [(0, 0), (0, 0)])

    def test_greedy_G3_uses_cap_then_narrow(self):
        # GREEDY, T = 4, Cmax = 1, G = 3, S = 0: general (3) beats narrow (2)
        # while the cap allows.  Turn 1: A k = 1 (fB = 3, cB = 1).
        # Turn 2: B e = 2, one general and one narrow: fA = 5, cA = 1.
        # Turn 3: A e = 2, cB at cap: fB = 3 + 4 = 7.  Turn 4: fA = 5 + 4 = 9.
        for tie in game.TIE_RULES:
            _, moves, end = solve(4, 1, 3, 0, "GREEDY", tie)
            self.assertEqual(moves, [(0, 1), (0, 1), (0, 0), (0, 0)])
            self.assertEqual(end, (9, 1, 7, 1))


# ----------------------------------------------------------------------------
# rules of game.py against the reference rules
# ----------------------------------------------------------------------------

class RulesAgainstReference(unittest.TestCase):

    def test_moves_and_steps(self):
        n = 0
        for Cmax in (1, 2, 3):
            for S in (0, 1, 2):
                for cA in range(Cmax + 1):
                    for cB in range(Cmax + 1):
                        for t in (1, 2):
                            state = (3, cA, 7, cB)
                            own, twin = (cA, cB) if t == 1 else (cB, cA)
                            mine = game.legal_moves(own, twin, Cmax, S)
                            ref = ref_moves(t, state, Cmax, S)
                            self.assertEqual(sorted(mine), sorted(ref))
                            for G in game.G_GRID:
                                for m in ref:
                                    self.assertEqual(
                                        game.apply_move(state, t, m, G),
                                        ref_step(t, state, m, G))
                                    n += 1
        self.assertGreater(n, 1000)

    def test_payoff(self):
        for base in game.BASES:
            for fA in range(0, 7):
                for fB in range(0, 7):
                    self.assertEqual(game.payoff(base, fA, fB),
                                     ref_payoff(base, (fA, 0, fB, 0)))

    def test_no_sabotage_move_at_zero(self):
        # S = 1 but the twin's c is 0: only sab = 0 is offered.
        self.assertEqual(game.legal_moves(0, 0, 2, 1), [(0, 0), (0, 1)])
        # twin at the cap with S = 1: a sabotage frees one slot.
        self.assertEqual(game.legal_moves(1, 2, 2, 1),
                         [(0, 0), (1, 0), (1, 1)])
        # S = 2 (supplement only): the sabotage does not free a slot.
        self.assertEqual(game.legal_moves(1, 2, 2, 2), [(0, 0), (1, 0)])


# ----------------------------------------------------------------------------
# (b) subgame perfection, checked directly by one-move deviations
# ----------------------------------------------------------------------------

class SubgamePerfection(unittest.TestCase):
    """For T <= 4 and Cmax <= 2, at EVERY turn and EVERY state (the states
    some move sequence reaches, plus a grid of states no sequence reaches),
    no single-move deviation by the mover raises its continuation payoff when
    play afterwards follows the solver.  For a finite game with perfect
    information this one-shot deviation test is equivalent to subgame
    perfection.  The continuation payoff is recomputed here by rolling the
    solver's policy forward with the reference rules; the solver's own value
    table is not trusted."""

    F_VALUES = (0, 1, 5)       # arbitrary f values for unreachable states

    def all_states(self, T, Cmax, G, S):
        layers = reachable_states(T, Cmax, G, S)
        n_reach = sum(len(v) for v in layers.values())
        out = {t: set(layers[t]) for t in layers}
        for t in range(1, T + 1):
            for cA in range(Cmax + 1):
                for cB in range(Cmax + 1):
                    for fA in self.F_VALUES:
                        for fB in self.F_VALUES:
                            out[t].add((fA, cA, fB, cB))
        return out, n_reach

    def run_check(self, literal, s_values=game.S_GRID):
        n_states = n_reach_total = n_dev = n_cases = 0
        for T in (2, 4):
            for Cmax in (1, 2):
                for G in game.G_GRID:
                    for S in s_values:
                        states, n_reach = self.all_states(T, Cmax, G, S)
                        for regime in game.SOLVED_REGIMES:
                            info = game.parse_regime(regime)
                            base, summed = info["base"], info["summed"]
                            for tie in game.TIE_RULES:
                                pl = game.make_player(T, Cmax, G, S, regime,
                                                      tie, literal=literal)
                                n_cases += 1
                                n_reach_total += n_reach
                                for t in range(1, T + 1):
                                    i = 0 if t % 2 == 1 else 1
                                    for s in states[t]:
                                        moves = ref_moves(t, s, Cmax, S)
                                        chosen = pl.policy(t, s)
                                        self.assertIn(chosen, moves)
                                        pay = {m: rollout(pl.policy, T, G, t,
                                                          s, m, base, summed)
                                               for m in moves}
                                        best = max(p[i] for p in pay.values())
                                        ctx = (T, Cmax, G, S, regime, tie, t,
                                               s)
                                        # no profitable one-move deviation
                                        self.assertEqual(pay[chosen][i], best,
                                                         ctx)
                                        # the tie rule picked among the best
                                        tied = [m for m in moves
                                                if pay[m][i] == best]
                                        want = min(tied, key=lambda m:
                                                   ref_tie_order(m, tie))
                                        self.assertEqual(chosen, want, ctx)
                                        # the solver's value is the rollout
                                        self.assertEqual(pl.value(t, s),
                                                         pay[chosen], ctx)
                                        n_states += 1
                                        n_dev += len(moves) - 1
        return n_cases, n_states, n_reach_total, n_dev

    def test_literal_solver(self):
        n_cases, n_states, n_reach, n_dev = self.run_check(literal=True)
        print("\n  [SPE literal solver] cases %d, decision nodes %d "
              "(of which reachable %d), deviations tried %d, improving 0"
              % (n_cases, n_states, n_reach, n_dev))
        self.assertEqual(n_cases, 384)

    def test_reduced_solver(self):
        n_cases, n_states, n_reach, n_dev = self.run_check(literal=False)
        print("\n  [SPE reduced solver] cases %d, decision nodes %d "
              "(of which reachable %d), deviations tried %d, improving 0"
              % (n_cases, n_states, n_reach, n_dev))
        self.assertEqual(n_cases, 384)

    def test_other_sabotage_reading(self):
        # S = 2 is outside the grid (report supplement V).  Same check.
        for literal in (True, False):
            n_cases, n_states, _n_reach, n_dev = self.run_check(
                literal=literal, s_values=(2,))
            print("\n  [SPE S = 2, %s solver] cases %d, decision nodes %d, "
                  "deviations tried %d, improving 0"
                  % ("literal" if literal else "reduced", n_cases, n_states,
                     n_dev))
            self.assertEqual(n_cases, 192)


# ----------------------------------------------------------------------------
# (c) first-best against the COLLECTIVE equilibrium
# ----------------------------------------------------------------------------

class FirstBest(unittest.TestCase):

    def check(self, t_values):
        n = 0
        for T in t_values:
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    best = exhaustive_best_total(T, Cmax, G, 0)
                    self.assertEqual(best, game.first_best(T, Cmax, G))
                    for tie in game.TIE_RULES:
                        for literal in (True, False):
                            pl, _, end = solve(T, Cmax, G, 0, "COLLECTIVE",
                                               tie, literal)
                            self.assertEqual(end[0] + end[2], best,
                                             (T, Cmax, G, tie, literal))
                            self.assertEqual(pl.value(1, START), (best, best))
                            n += 1
        return n

    def test_exhaustive_equals_collective_T_up_to_8(self):
        # required: every grid case with T <= 8
        n = self.check([T for T in game.T_GRID if T <= 8])
        print("\n  [first-best] T <= 8: %d solver runs equal the exhaustive "
              "search" % n)
        self.assertEqual(n, 4 * 3 * 4 * 2 * 2)

    def test_exhaustive_equals_collective_T_10_12(self):
        # extra: the two largest horizons as well
        n = self.check([T for T in game.T_GRID if T > 8])
        print("\n  [first-best] T in {10, 12}: %d solver runs equal the "
              "exhaustive search" % n)

    def test_with_sabotage_small(self):
        # With S = 1 COLLECTIVE is still a team problem.  For T <= 6 the
        # exhaustive search over sequences WITH sabotage is cheap enough.
        n = 0
        for T in (2, 4, 6):
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    best = exhaustive_best_total(T, Cmax, G, 1)
                    self.assertGreaterEqual(
                        best, exhaustive_best_total(T, Cmax, G, 0))
                    for tie in game.TIE_RULES:
                        _pl, _, end = solve(T, Cmax, G, 1, "COLLECTIVE", tie)
                        self.assertEqual(end[0] + end[2], best)
                        n += 1
        print("\n  [first-best] S = 1, T <= 6: %d solver runs equal the "
              "exhaustive search with sabotage" % n)

    def test_no_regime_beats_first_best_without_sabotage(self):
        for T in game.T_GRID:
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    fb = game.first_best(T, Cmax, G)
                    for regime in game.REGIMES:
                        for tie in game.TIE_RULES:
                            _, _, end = solve(T, Cmax, G, 0, regime, tie,
                                              literal=False)
                            self.assertLessEqual(end[0] + end[2], fb)


# ----------------------------------------------------------------------------
# (d) RIVAL is zero-sum at every node
# ----------------------------------------------------------------------------

class RivalZeroSum(unittest.TestCase):

    def test_every_node(self):
        n_lit = n_red = 0
        for T in game.T_GRID:
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    for S in game.S_GRID:
                        for regime in ("RIVAL", "RIVAL_SUM"):
                            for tie in game.TIE_RULES:
                                lit = game.make_player(T, Cmax, G, S, regime,
                                                       tie, literal=True)
                                lit.node(1, START)
                                for uA, uB, _ in lit.memo.values():
                                    self.assertEqual(uA + uB, 0)
                                    n_lit += 1
                                red = game.make_player(T, Cmax, G, S, regime,
                                                       tie, literal=False)
                                for t in range(1, T + 1):
                                    for cA in range(Cmax + 1):
                                        for cB in range(Cmax + 1):
                                            wA, wB, _ = red.node(t, cA, cB)
                                            self.assertEqual(wA + wB, 0)
                                            n_red += 1
        print("\n  [zero-sum] literal nodes %d, reduced nodes %d, all sum "
              "to 0" % (n_lit, n_red))


# ----------------------------------------------------------------------------
# the two solvers, the myopic rules, the report helpers, the JSON file
# ----------------------------------------------------------------------------

class SolverAgreement(unittest.TestCase):

    def test_literal_equals_reduced_T_up_to_8(self):
        n = 0
        for T in (2, 4, 6, 8):
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    for S in game.S_GRID:
                        for regime in game.SOLVED_REGIMES:
                            for tie in game.TIE_RULES:
                                a = solve(T, Cmax, G, S, regime, tie, True)
                                b = solve(T, Cmax, G, S, regime, tie, False)
                                self.assertEqual(a[1:], b[1:])
                                self.assertEqual(a[0].value(1, START),
                                                 b[0].value(1, START))
                                n += 1
        self.assertEqual(n, 4 * 3 * 4 * 2 * 6 * 2)

    def test_literal_equals_reduced_other_sabotage_reading(self):
        # supplement V uses the reduced solver with S = 2
        for T in (2, 4, 6):
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    for regime in game.SOLVED_REGIMES:
                        for tie in game.TIE_RULES:
                            a = solve(T, Cmax, G, 2, regime, tie, True)
                            b = solve(T, Cmax, G, 2, regime, tie, False)
                            self.assertEqual(a[1:], b[1:])

    def test_literal_equals_reduced_without_cap(self):
        # the no-cap supplement uses the reduced solver; check it against
        # the literal one for the horizons where the literal one is cheap
        for T in (2, 4, 6):
            for G in game.G_GRID:
                for regime in game.UNCAPPED_REGIMES:
                    for tie in game.TIE_RULES:
                        a = solve(T, game.NO_CAP, G, 0, regime, tie, True)
                        b = solve(T, game.NO_CAP, G, 0, regime, tie, False)
                        self.assertEqual(a[1:], b[1:])

    def test_f_does_not_change_the_move(self):
        # the lemma behind the reduced solver, on the literal solver
        for regime in game.SOLVED_REGIMES:
            for tie in game.TIE_RULES:
                lit = game.make_player(4, 2, 1, 1, regime, tie, literal=True)
                for t in range(1, 5):
                    for cA in range(3):
                        for cB in range(3):
                            ref = lit.policy(t, (0, cA, 0, cB))
                            for fA, fB in ((9, 0), (0, 9), (4, 7), (13, 2)):
                                self.assertEqual(
                                    lit.policy(t, (fA, cA, fB, cB)), ref)


class MyopicRules(unittest.TestCase):

    def test_roundtrip_zero_is_greedy(self):
        for T in game.T_GRID:
            for Cmax in game.CMAX_GRID:
                for G in game.G_GRID:
                    for S in game.S_GRID:
                        for tie in game.TIE_RULES:
                            a = solve(T, Cmax, G, S, "GREEDY", tie)
                            b = solve(T, Cmax, G, S, "ROUNDTRIP(0)", tie)
                            self.assertEqual(a[1:], b[1:])

    def test_roundtrip_last_turn_is_greedy(self):
        for gamma in game.GAMMAS:
            for G in game.G_GRID:
                rt = game.MyopicRule(4, 2, G, 1, gamma, "min_general")
                gr = game.MyopicRule(4, 2, G, 1, None, "min_general")
                for cA in range(3):
                    for cB in range(3):
                        s = (1, cA, 2, cB)
                        self.assertEqual(rt.policy(4, s), gr.policy(4, s))

    def test_greedy_is_myopically_optimal(self):
        for G in game.G_GRID:
            for S in game.S_GRID:
                rule = game.MyopicRule(4, 2, G, S, None, "max_general")
                for t in (1, 2):
                    for cA in range(3):
                        for cB in range(3):
                            s = (0, cA, 0, cB)
                            j = 2 if t == 1 else 0
                            best = max(ref_step(t, s, m, G)[j]
                                       for m in ref_moves(t, s, 2, S))
                            got = ref_step(t, s, rule.policy(t, s), G)[j]
                            self.assertEqual(got, best)


class ReportHelpers(unittest.TestCase):

    def expand(self, boxes, domain):
        """Elements of the domain covered by the boxes."""
        covered = []
        for cons, n, exact in boxes:
            self.assertTrue(exact)
            hit = [d for d in domain
                   if all(d[x] in vals for x, vals in cons)]
            self.assertEqual(len(hit), n)
            covered.extend(id(d) for d in hit)
        return covered

    def test_describe_exceptions_is_exact(self):
        dims = ("a", "b", "c", "d")
        domain = [{"a": a, "b": b, "c": c, "d": d}
                  for a in range(3) for b in range(4)
                  for c in ("x", "y") for d in range(3)]
        patterns = [
            lambda d: False,
            lambda d: True,
            lambda d: d["a"] == 1,
            lambda d: d["a"] == 1 and d["c"] == "x",
            lambda d: d["a"] == 1 or (d["b"] == 2 and d["c"] == "y"),
            lambda d: (d["a"] + d["b"] + d["d"]) % 2 == 0,
            lambda d: (d["a"] * 7 + d["b"] * 5 + d["d"] * 3
                       + (d["c"] == "x")) % 5 == 0,
            lambda d: d["b"] >= 2 and not (d["a"] == 0 and d["d"] == 1),
        ]
        for pat in patterns:
            flags = [pat(d) for d in domain]
            boxes = game.describe_exceptions(domain, flags, dims)
            covered = self.expand(boxes, domain)
            want = [id(d) for d, f in zip(domain, flags) if f]
            self.assertEqual(len(covered), len(set(covered)))   # disjoint
            self.assertEqual(sorted(covered), sorted(want))

    def test_describe_exceptions_single_box(self):
        dims = ("a", "b")
        domain = [{"a": a, "b": b} for a in range(3) for b in range(3)]
        flags = [d["a"] == 2 for d in domain]
        self.assertEqual(game.describe_exceptions(domain, flags, dims),
                         [((("a", (2,)),), 3, True)])

    def test_describe_exceptions_marks_inseparable(self):
        dims = ("a",)
        domain = [{"a": 0}, {"a": 0}, {"a": 1}]
        boxes = game.describe_exceptions(domain, [True, False, False], dims)
        self.assertEqual(len(boxes), 1)
        self.assertFalse(boxes[0][2])
        self.assertEqual(boxes[0][1], 1)

    def test_evaluate_verdict_words(self):
        domain = [{"T": T, "Cmax": 1, "G": G, "S": 0, "tie": tie}
                  for T in (2, 4) for G in (0, 1) for tie in game.TIE_RULES]
        self.assertEqual(game.evaluate("x", "", domain,
                                       lambda d: True)["kind"], "FOLLOWS")
        self.assertEqual(game.evaluate("x", "", domain,
                                       lambda d: False)["kind"], "FAILS")
        res = game.evaluate("x", "", domain,
                            lambda d: d["tie"] == "min_general")
        self.assertEqual(res["kind"], "DEPENDS on tie")
        self.assertEqual((res["cfg_hold"], res["cfg_n"]), (0, 4))
        self.assertEqual(game.evaluate("x", "", [],
                                       lambda d: True)["kind"], "VACUOUS")


class JsonFile(unittest.TestCase):
    """game_cases.json, if present, must match a fresh solve."""

    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "game_cases.json")

    def test_rows_match_fresh_solve(self):
        if not os.path.exists(self.PATH):
            self.skipTest("game_cases.json not generated yet")
        with open(self.PATH) as fh:
            data = json.load(fh)
        cases = data["cases"]
        self.assertEqual(len(cases), 6 * 3 * 4 * 2 * 11 * 2)
        keys = set()
        for row in cases:
            keys.add((row["T"], row["Cmax"], row["G"], row["S"],
                      row["regime"], row["tie"]))
            _, moves, end = solve(row["T"], row["Cmax"], row["G"], row["S"],
                                  row["regime"], row["tie"], literal=False)
            self.assertEqual([(s["sab"], s["k"]) for s in row["path"]], moves)
            self.assertEqual((row["end"]["fA"], row["end"]["cA"],
                              row["end"]["fB"], row["end"]["cB"]), end)
            self.assertEqual(row["end_score"], end[0] + end[2])
            self.assertEqual(Fraction(row["efficiency_exact"]),
                             Fraction(end[0] + end[2], row["first_best"]))
            self.assertEqual(row["general_A"] + row["general_B"],
                             sum(k for _, k in moves))
            self.assertEqual(row["sabotage_events"],
                             sum(sab for sab, _ in moves))
            # effort recorded per turn is 1 + the mover's c at that time
            s = START
            for step in row["path"]:
                own = s[1] if step["t"] % 2 == 1 else s[3]
                self.assertEqual(step["e"], 1 + own)
                self.assertEqual(step["mover"],
                                 "A" if step["t"] % 2 == 1 else "B")
                s = ref_step(step["t"], s, (step["sab"], step["k"]),
                             row["G"])
        self.assertEqual(len(keys), len(cases))


if __name__ == "__main__":
    unittest.main(verbosity=2)
