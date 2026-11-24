#!/usr/bin/env python3
"""Gemini cells game: an exact model of two twin cells that improve each other.

Run `python3 game.py` to solve the whole grid, print the report to stdout and
write `game_cases.json` next to this file.  Standard library only.  No
randomness.  All payoffs are exact integers or `fractions.Fraction`.
Timing goes to stderr so that stdout is the same on every run.

THE MODEL
---------
State: integers (fA, cA, fB, cB), all 0 at the start, and a turn t = 1..T.
A moves on odd t, B on even t.  T is even.

On its move the mover i (twin j) has e = 1 + c_i effort units.  Each unit is
spent on exactly one of
    narrow :  f_j += 2
    general:  c_j += 1 (capped at Cmax) and f_j += G        G in {0,1,2,3}
so a move is the number k of general units, 0 <= k <= min(e, Cmax - c_j).
With sabotage (S = 1) the mover may also lower c_j by 1 first, at no effort
cost.  A move is then (sab, k) and the cap is checked after the sabotage:
0 <= k <= min(e, Cmax - (c_j - sab)).
(S = 2, outside the grid, is the other reading: the cap room is counted
before the sabotage.  It is used in one supplement of the report only.)

Scoring regimes: see `REGIMES` and the README.

SOLVERS
-------
`LiteralSolver`  backward induction memoised on (t, fA, cA, fB, cB).  This is
                 the solver that produces every equilibrium path in the grid.
`ReducedSolver`  backward induction memoised on (t, cA, cB).  A second,
                 independent memoisation used as a cross-check and for cheap
                 look-ups of off-path moves.
They must agree because every payoff is linear in (fA, fB), the c-dynamics and
the legal moves do not depend on f, and ties are broken by the move label
only.  So f only adds a constant, the same for every move at a node, to each
player's continuation payoff.  `run_grid` checks the agreement at every node
the literal solver visits.
"""

from fractions import Fraction
import json
import os
import sys
import time

# ----------------------------------------------------------------------------
# Grid
# ----------------------------------------------------------------------------

NARROW_GAIN = 2            # f is in half-units: a narrow unit is worth 2
T_GRID = (2, 4, 6, 8, 10, 12)
CMAX_GRID = (1, 2, 3)
G_GRID = (0, 1, 2, 3)
S_GRID = (0, 1)
TIE_RULES = ("min_general", "max_general")
GAMMAS = (Fraction(0), Fraction(1, 2), Fraction(1), Fraction(2))
BASES = ("CROSS", "RIVAL", "COLLECTIVE")


def gamma_label(g):
    """0 -> '0', 1/2 -> '0.5', 1 -> '1', 2 -> '2'."""
    g = Fraction(g)
    return str(g.numerator) if g.denominator == 1 else str(float(g))


REGIMES = (
    ["CROSS", "RIVAL", "COLLECTIVE", "GREEDY"]
    + ["ROUNDTRIP(%s)" % gamma_label(g) for g in GAMMAS]
    + ["CROSS_SUM", "RIVAL_SUM", "COLLECTIVE_SUM"]
)
SOLVED_REGIMES = ("CROSS", "RIVAL", "COLLECTIVE",
                  "CROSS_SUM", "RIVAL_SUM", "COLLECTIVE_SUM")


def parse_regime(regime):
    """Return a dict describing the regime label."""
    if regime in BASES:
        return {"kind": "equilibrium", "base": regime, "summed": False}
    if regime.endswith("_SUM") and regime[:-4] in BASES:
        return {"kind": "equilibrium", "base": regime[:-4], "summed": True}
    if regime == "GREEDY":
        return {"kind": "myopic", "gamma": None}
    if regime.startswith("ROUNDTRIP(") and regime.endswith(")"):
        return {"kind": "myopic", "gamma": Fraction(regime[10:-1])}
    raise ValueError("unknown regime %r" % (regime,))


# ----------------------------------------------------------------------------
# Rules of the game
# ----------------------------------------------------------------------------

def mover_of(t):
    """0 for A (odd turns), 1 for B (even turns)."""
    return 0 if t % 2 == 1 else 1


def legal_moves(c_mover, c_twin, Cmax, S):
    """All moves (sab, k) open to a mover with builder capability c_mover
    whose twin has builder capability c_twin.

    sab = 1 is offered only when S >= 1 and c_twin >= 1.  At c_twin = 0 a
    sabotage would change nothing, so it is not listed as a separate move.

    S = 1 is the model: the sabotage is applied first and the cap is checked
    on the lowered c, so 0 <= k <= min(e, Cmax - (c_twin - sab)).
    S = 2 is NOT in the requested grid.  It is the other reading of the
    sabotage rule, used only in a supplement: the room for general units is
    counted before the sabotage, 0 <= k <= min(e, Cmax - c_twin).
    """
    e = 1 + c_mover
    out = []
    for sab in ((0, 1) if (S >= 1 and c_twin >= 1) else (0,)):
        room = Cmax - c_twin + (sab if S == 1 else 0)
        for k in range(min(e, room) + 1):
            out.append((sab, k))
    return out


def apply_move(state, t, move, G):
    """State after the mover of turn t plays move = (sab, k)."""
    fA, cA, fB, cB = state
    sab, k = move
    if t % 2 == 1:                       # A moves and changes B's harness
        e = 1 + cA
        return (fA, cA, fB + G * k + NARROW_GAIN * (e - k), cB - sab + k)
    e = 1 + cB                           # B moves and changes A's harness
    return (fA + G * k + NARROW_GAIN * (e - k), cA - sab + k, fB, cB)


def payoff(base, fA, fB):
    """(u_A, u_B) of a state under one of the three base scoring rules."""
    if base == "CROSS":
        return (fB, fA)
    if base == "RIVAL":
        return (fB - fA, fA - fB)
    if base == "COLLECTIVE":
        return (fA + fB, fA + fB)
    raise ValueError(base)


def tie_rank(move, tie):
    """Lower rank is preferred among moves with equal objective."""
    sab, k = move
    if tie == "min_general":
        return (k, sab)
    if tie == "max_general":
        return (-k, sab)
    raise ValueError(tie)


def pick(scored, tie):
    """scored: list of (objective, move, payload).  Highest objective wins;
    equal objectives are resolved by the tie rule."""
    best = None
    for item in scored:
        if (best is None or item[0] > best[0]
                or (item[0] == best[0]
                    and tie_rank(item[1], tie) < tie_rank(best[1], tie))):
            best = item
    return best


# ----------------------------------------------------------------------------
# Subgame-perfect equilibrium by backward induction
# ----------------------------------------------------------------------------

class LiteralSolver:
    """Backward induction memoised on the full state (t, fA, cA, fB, cB)."""

    def __init__(self, T, Cmax, G, S, base, summed, tie):
        self.T, self.Cmax, self.G, self.S = T, Cmax, G, S
        self.base, self.summed, self.tie = base, summed, tie
        self.memo = {}

    def node(self, t, state):
        """(uA, uB, move) at the start of turn t in `state`.
        End scoring: (uA, uB) is the final payoff.  Summed scoring: the
        payoff summed over the states after turns t..T."""
        if t > self.T:
            if self.summed:
                return (0, 0, None)
            u = payoff(self.base, state[0], state[2])
            return (u[0], u[1], None)
        key = (t,) + state
        hit = self.memo.get(key)
        if hit is not None:
            return hit
        i = mover_of(t)
        c_m, c_t = (state[1], state[3]) if i == 0 else (state[3], state[1])
        scored = []
        for move in legal_moves(c_m, c_t, self.Cmax, self.S):
            s2 = apply_move(state, t, move, self.G)
            nA, nB, _ = self.node(t + 1, s2)
            if self.summed:
                u = payoff(self.base, s2[0], s2[2])
                val = (u[0] + nA, u[1] + nB)
            else:
                val = (nA, nB)
            scored.append((val[i], move, val))
        _, move, val = pick(scored, self.tie)
        res = (val[0], val[1], move)
        self.memo[key] = res
        return res

    def policy(self, t, state):
        return self.node(t, state)[2]

    def value(self, t, state):
        r = self.node(t, state)
        return (r[0], r[1])


class ReducedSolver:
    """Backward induction memoised on (t, cA, cB).

    node(t, cA, cB) = (wA, wB, move): the continuation payoffs of A and B
    from the start of turn t when fA = fB = 0, and the mover's move.  For a
    state with other f the continuation payoff is
        weight(t) * payoff(fA, fB) + (wA, wB)
    with weight(t) = 1 for end scoring and T - t + 1 for summed scoring.
    """

    def __init__(self, T, Cmax, G, S, base, summed, tie):
        self.T, self.Cmax, self.G, self.S = T, Cmax, G, S
        self.base, self.summed, self.tie = base, summed, tie
        self.memo = {}

    def weight(self, t):
        return (self.T - t + 1) if self.summed else 1

    def node(self, t, cA, cB):
        if t > self.T:
            return (0, 0, None)
        key = (t, cA, cB)
        hit = self.memo.get(key)
        if hit is not None:
            return hit
        i = mover_of(t)
        c_m, c_t = (cA, cB) if i == 0 else (cB, cA)
        w = self.weight(t)
        scored = []
        for move in legal_moves(c_m, c_t, self.Cmax, self.S):
            dA, cA2, dB, cB2 = apply_move((0, cA, 0, cB), t, move, self.G)
            inc = payoff(self.base, dA, dB)
            nA, nB, _ = self.node(t + 1, cA2, cB2)
            val = (w * inc[0] + nA, w * inc[1] + nB)
            scored.append((val[i], move, val))
        _, move, val = pick(scored, self.tie)
        res = (val[0], val[1], move)
        self.memo[key] = res
        return res

    def policy(self, t, state):
        return self.node(t, state[1], state[3])[2]

    def value(self, t, state):
        fA, cA, fB, cB = state
        wA, wB, _ = self.node(t, cA, cB)
        base = payoff(self.base, fA, fB)
        w = self.weight(t)
        return (w * base[0] + wA, w * base[1] + wB)


# ----------------------------------------------------------------------------
# Myopic rules: GREEDY and ROUNDTRIP(gamma)
# ----------------------------------------------------------------------------

class MyopicRule:
    """GREEDY (gamma is None) or ROUNDTRIP(gamma).  Not an equilibrium: each
    mover follows a fixed rule and the play is simulated forward."""

    def __init__(self, T, Cmax, G, S, gamma, tie):
        self.T, self.Cmax, self.G, self.S = T, Cmax, G, S
        self.gamma, self.tie = gamma, tie

    def _options(self, t, state):
        i = mover_of(t)
        c_m, c_t = (state[1], state[3]) if i == 0 else (state[3], state[1])
        f_idx = 2 if i == 0 else 0       # index of the twin's f
        out = []
        for move in legal_moves(c_m, c_t, self.Cmax, self.S):
            s2 = apply_move(state, t, move, self.G)
            out.append((s2[f_idx] - state[f_idx], move, s2))
        return out

    def greedy_gain(self, t, state):
        """Largest immediate gain in the twin's f the mover of turn t can
        make.  It does not depend on the tie rule."""
        return max(gain for gain, _, _ in self._options(t, state))

    def objective(self, t, state):
        """List of (objective, move, next_state)."""
        out = []
        for gain, move, s2 in self._options(t, state):
            obj = gain
            if self.gamma is not None and t < self.T:
                obj = gain + self.gamma * self.greedy_gain(t + 1, s2)
            out.append((obj, move, s2))
        return out

    def policy(self, t, state):
        return pick(self.objective(t, state), self.tie)[1]


# ----------------------------------------------------------------------------
# Playing a case
# ----------------------------------------------------------------------------

def make_player(T, Cmax, G, S, regime, tie, literal=True):
    """The object whose .policy(t, state) gives the mover's move."""
    info = parse_regime(regime)
    if info["kind"] == "equilibrium":
        cls = LiteralSolver if literal else ReducedSolver
        return cls(T, Cmax, G, S, info["base"], info["summed"], tie)
    return MyopicRule(T, Cmax, G, S, info["gamma"], tie)


def play(player, start=(0, 0, 0, 0), t_start=1):
    """Follow player.policy from `start`.  Returns (path, states): path is a
    list of (t, mover, sab, k, e); states[n] is the state after the n-th
    listed turn and states[0] is the start."""
    state = start
    path = []
    states = [state]
    for t in range(t_start, player.T + 1):
        sab, k = player.policy(t, state)
        e = 1 + (state[1] if t % 2 == 1 else state[3])
        path.append((t, "A" if t % 2 == 1 else "B", sab, k, e))
        state = apply_move(state, t, (sab, k), player.G)
        states.append(state)
    return path, states


def first_best(T, Cmax, G):
    """Largest fA_end + fB_end over ALL move sequences without sabotage.
    Plain exhaustive depth-first enumeration: no memo and no solver."""
    best = [-1]

    def rec(t, state):
        if t > T:
            if state[0] + state[2] > best[0]:
                best[0] = state[0] + state[2]
            return
        c_m, c_t = (state[1], state[3]) if t % 2 == 1 else (state[3], state[1])
        for move in legal_moves(c_m, c_t, Cmax, 0):
            rec(t + 1, apply_move(state, t, move, G))

    rec(1, (0, 0, 0, 0))
    return best[0]


def solve_case(T, Cmax, G, S, regime, tie, fb, literal=True):
    """Solve one case.  Returns (row, player)."""
    player = make_player(T, Cmax, G, S, regime, tie, literal=literal)
    path, states = play(player)
    fA, cA, fB, cB = states[-1]
    info = parse_regime(regime)
    row = {
        "T": T, "Cmax": Cmax, "G": G, "S": S, "regime": regime,
        "gamma": (None if info.get("gamma") is None
                  else str(info["gamma"])),
        "tie": tie,
        "path": [{"t": t, "mover": m, "sab": sab, "k": k, "e": e}
                 for (t, m, sab, k, e) in path],
        "general_A": sum(k for (t, m, sab, k, e) in path if m == "A"),
        "general_B": sum(k for (t, m, sab, k, e) in path if m == "B"),
        "sabotage_A": sum(sab for (t, m, sab, k, e) in path if m == "A"),
        "sabotage_B": sum(sab for (t, m, sab, k, e) in path if m == "B"),
        "end": {"fA": fA, "cA": cA, "fB": fB, "cB": cB},
        "end_score": fA + fB,
        "first_best": fb,
    }
    row["general_total"] = row["general_A"] + row["general_B"]
    row["sabotage_events"] = row["sabotage_A"] + row["sabotage_B"]
    eff = Fraction(fA + fB, fb)
    row["efficiency"] = round(float(eff), 6)
    row["efficiency_exact"] = "%d/%d" % (eff.numerator, eff.denominator)
    if info["kind"] == "equilibrium":
        uA, uB = player.value(1, (0, 0, 0, 0))
        row["payoff_A"], row["payoff_B"] = uA, uB
    else:
        row["payoff_A"], row["payoff_B"] = None, None
    row["_states"] = states              # private: not written to JSON
    return row, player


def crosscheck_case(lit, row):
    """Compare a solved LiteralSolver with a fresh ReducedSolver.

    Returns (reduced_solver, reachable_nodes, offpath_nodes, zero_sum_nodes).
    Raises AssertionError on any disagreement.
    """
    red = ReducedSolver(lit.T, lit.Cmax, lit.G, lit.S, lit.base, lit.summed,
                        lit.tie)
    # 1. every node the literal solver visited from the start state
    reachable = 0
    for key, (uA, uB, move) in list(lit.memo.items()):
        t, state = key[0], key[1:]
        if red.policy(t, state) != move or red.value(t, state) != (uA, uB):
            raise AssertionError("literal/reduced mismatch at %r" % (key,))
        reachable += 1
    # 2. the same path
    _path, states = play(red)
    if states != row["_states"]:
        raise AssertionError("literal/reduced path mismatch")
    # 3. every (t, cA, cB), reachable or not, with fA = fB = 0
    offpath = 0
    for t in range(1, lit.T + 1):
        for cA in range(lit.Cmax + 1):
            for cB in range(lit.Cmax + 1):
                state = (0, cA, 0, cB)
                uA, uB, move = lit.node(t, state)
                if (red.policy(t, state) != move
                        or red.value(t, state) != (uA, uB)):
                    raise AssertionError("literal/reduced mismatch at %r"
                                         % ((t,) + state,))
                offpath += 1
    # 4. RIVAL is zero-sum at every node in the literal memo
    zero_sum = 0
    if lit.base == "RIVAL":
        for key, (uA, uB, move) in lit.memo.items():
            if uA + uB != 0:
                raise AssertionError("RIVAL not zero-sum at %r" % (key,))
            zero_sum += 1
    return red, reachable, offpath, zero_sum


def run_grid(crosscheck=True):
    """Solve every case of the grid.

    Returns (rows, index, players, fb, checks).  `players` maps a case key to
    a small object with .policy(t, state): the ReducedSolver for equilibrium
    regimes (checked against the literal one when crosscheck is True) and the
    MyopicRule otherwise.
    """
    fb = {}
    for T in T_GRID:
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                fb[(T, Cmax, G)] = first_best(T, Cmax, G)
    checks = {"cases_checked": 0, "reachable_nodes": 0, "offpath_nodes": 0,
              "zero_sum_nodes": 0}
    rows, index, players = [], {}, {}
    for T in T_GRID:
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                for S in S_GRID:
                    for regime in REGIMES:
                        for tie in TIE_RULES:
                            row, player = solve_case(
                                T, Cmax, G, S, regime, tie, fb[(T, Cmax, G)])
                            key = (T, Cmax, G, S, regime, tie)
                            if isinstance(player, LiteralSolver):
                                if crosscheck:
                                    red, n1, n2, n3 = crosscheck_case(
                                        player, row)
                                    checks["cases_checked"] += 1
                                    checks["reachable_nodes"] += n1
                                    checks["offpath_nodes"] += n2
                                    checks["zero_sum_nodes"] += n3
                                else:
                                    red = make_player(T, Cmax, G, S, regime,
                                                      tie, literal=False)
                                player = red   # drop the big literal memo
                            rows.append(row)
                            index[key] = row
                            players[key] = player
    # does the path differ between the two tie rules?
    for row in rows:
        other_tie = TIE_RULES[1 - TIE_RULES.index(row["tie"])]
        other = index[(row["T"], row["Cmax"], row["G"], row["S"],
                       row["regime"], other_tie)]
        row["path_differs_across_tie_rules"] = row["path"] != other["path"]
        row["end_differs_across_tie_rules"] = row["end"] != other["end"]
        row["score_differs_across_tie_rules"] = (
            row["end_score"] != other["end_score"])
    return rows, index, players, fb, checks


# ----------------------------------------------------------------------------
# Describing sets of cases exactly
# ----------------------------------------------------------------------------

CASE_DIMS = ("T", "Cmax", "G", "S", "tie")


def _sorted_vals(vals):
    return tuple(sorted(vals, key=lambda v: (isinstance(v, str), v)))


def fmt_vals(vals):
    vals = _sorted_vals(vals)
    if len(vals) == 1:
        return str(vals[0])
    return "{" + ",".join(str(v) for v in vals) + "}"


def describe_exceptions(domain, flags, dims):
    """Describe exactly which elements of `domain` are flagged.

    domain: list of dicts.  flags: list of bool, True = exception.
    Returns a list of boxes (constraints, count, exact).  `constraints` is a
    tuple of (dim, values).  A box stands for every element of the domain
    whose listed dims take one of the listed values; dims not listed are
    free.  The boxes are disjoint and their union is exactly the flagged
    set.  The search prefers the description with the fewest boxes.

    If two elements agree on every dim but only one is flagged, the dims
    cannot separate them.  Then the box is marked exact = False and carries
    the pseudo-constraint '(part)' = 'n of m': n of the m elements in that
    box are exceptions.
    """
    cells = {}
    for d, flag in zip(domain, flags):
        key = tuple(d[x] for x in dims)
        cell = cells.setdefault(key, [0, 0])
        cell[0] += 1
        cell[1] += 1 if flag else 0
    all_cells = [(key, n, m) for key, (n, m) in cells.items()]
    memo = {}

    def solve(cl, free, fixed):
        if fixed in memo:
            return memo[fixed]
        exc = [c for c in cl if c[2] > 0]
        n_exc = sum(c[2] for c in exc)
        if not exc:
            res = []
        else:
            sub_vals = {i: {c[0][i] for c in exc} for i in free}
            dom_vals = {i: {c[0][i] for c in cl} for i in free}
            n_box = sum(c[1] for c in cl
                        if all(c[0][i] in sub_vals[i] for i in free))
            cons = tuple((dims[i], _sorted_vals(sub_vals[i])) for i in free
                         if sub_vals[i] != dom_vals[i])
            splittable = [i for i in free if len(dom_vals[i]) > 1]
            if n_box == n_exc:
                res = [(cons, n_exc, True)]
            elif not splittable:
                res = [(cons + (("(part)", ("%d of %d" % (n_exc, n_box),)),),
                        n_exc, False)]
            else:
                best = None
                for i in splittable:
                    rest = tuple(j for j in free if j != i)
                    groups = []          # [signature, [values], boxes]
                    for v in _sorted_vals(sub_vals[i]):
                        boxes = solve([c for c in cl if c[0][i] == v], rest,
                                      fixed | frozenset([(i, v)]))
                        sig = tuple(c for c, _, _ in boxes)
                        hit = None
                        if all(ex for _, _, ex in boxes):
                            for g in groups:
                                if g[0] == sig:
                                    hit = g
                                    break
                        if hit is None:
                            groups.append([sig, [v], boxes])
                        else:
                            hit[1].append(v)
                            hit[2] = [(c, n0 + n1, True) for (c, n0, _), (_, n1, _)
                                      in zip(hit[2], boxes)]
                        if not all(ex for _, _, ex in boxes):
                            groups[-1][0] = None     # never merge inexact
                    pieces = []
                    for sig, vals, boxes in groups:
                        # a merged group that covers every value of this dim
                        # needs no constraint on it
                        head = (() if set(vals) == dom_vals[i]
                                else ((dims[i], tuple(vals)),))
                        for c, n, ex in boxes:
                            pieces.append((head + c, n, ex))
                    cost = (sum(1 for x in pieces if not x[2]), len(pieces),
                            sum(len(x[0]) for x in pieces))
                    if best is None or cost < best[0]:
                        best = (cost, pieces)
                res = best[1]
        memo[fixed] = res
        return res

    return solve(all_cells, tuple(range(len(dims))), frozenset())


def box_text(cons):
    if not cons:
        return "every case of the domain"
    return ", ".join("%s=%s" % (x, fmt_vals(v)) for x, v in cons)


def evaluate(cid, statement, domain, pred, dims=CASE_DIMS, unit="cases"):
    """Evaluate a yes/no statement on every element of a domain."""
    flags = [not pred(d) for d in domain]
    n, n_exc = len(domain), sum(flags)
    res = {"id": cid, "statement": statement, "unit": unit,
           "n": n, "n_hold": n - n_exc,
           "boxes": describe_exceptions(domain, flags, dims)}
    if n == 0:
        res["kind"] = "VACUOUS"
        verdict = "VACUOUS (the domain is empty)"
    elif n_exc == 0:
        res["kind"] = "FOLLOWS"
        verdict = "FOLLOWS in the model"
    elif n_exc == n:
        res["kind"] = "FAILS"
        verdict = "FAILS in the model (in every case of the domain)"
    else:
        names = []
        for cons, _, _ in res["boxes"]:
            for x, _v in cons:
                if x not in names and x != "(part)":
                    names.append(x)
        names.sort(key=lambda x: dims.index(x))
        res["kind"] = "DEPENDS on %s" % ", ".join(names)
        verdict = "%s (holds in %d of %d)" % (res["kind"], n - n_exc, n)
    res["verdict"] = verdict
    # In how many parameter configurations does it hold under BOTH tie
    # rules?  Only reported when every configuration has both of its cases
    # in the domain.
    if "tie" in dims and unit == "cases" and n:
        cfg = {}
        for d, flag in zip(domain, flags):
            cfg.setdefault(tuple(d[x] for x in dims if x != "tie"),
                           []).append(not flag)
        if all(len(v) == len(TIE_RULES) for v in cfg.values()):
            res["cfg_n"] = len(cfg)
            res["cfg_hold"] = sum(1 for v in cfg.values() if all(v))
    return res


# ----------------------------------------------------------------------------
# Report helpers
# ----------------------------------------------------------------------------

def table(headers, body):
    """Plain text table: first column left aligned, the others right."""
    cells = [[str(c) for c in row] for row in body]
    widths = [len(str(h)) for h in headers]
    for row in cells:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(c))

    def fmt(row):
        return "  ".join(c.ljust(w) if i == 0 else c.rjust(w)
                         for i, (c, w) in enumerate(zip(row, widths))).rstrip()

    return ([fmt([str(h) for h in headers]),
             "  ".join("-" * w for w in widths)]
            + [fmt(r) for r in cells])


def f4(x):
    return "%.4f" % float(x)


def mean(xs):
    xs = list(xs)
    return sum(xs, Fraction(0)) / len(xs)


def k_string(row):
    return "".join(str(s["k"]) for s in row["path"])


def sab_string(row):
    return "".join(str(s["sab"]) for s in row["path"])


def e_string(row):
    return "".join(str(s["e"]) for s in row["path"])


def rows_of(rows, regime, **conds):
    out = []
    for r in rows:
        if r["regime"] != regime:
            continue
        ok = True
        for key, want in conds.items():
            if isinstance(want, (tuple, list, set, frozenset)):
                ok = r[key] in want
            else:
                ok = r[key] == want
            if not ok:
                break
        if ok:
            out.append(r)
    return out


def switch_turn(row):
    """Last turn with k > 0, or 0 if there is none."""
    last = 0
    for s in row["path"]:
        if s["k"] > 0:
            last = s["t"]
    return last


def print_result(p, res, prefix=""):
    p("[%s%s] %s" % (prefix, res["id"], res["statement"]))
    p("    holds in %d of %d %s" % (res["n_hold"], res["n"], res["unit"]))
    if "cfg_n" in res:
        p("    holds under both tie rules in %d of %d parameter "
          "configurations" % (res["cfg_hold"], res["cfg_n"]))
    if res["boxes"]:
        p("    exceptions (%d):" % (res["n"] - res["n_hold"]))
        for cons, n, _exact in res["boxes"]:
            p("      - %s  [%d]" % (box_text(cons), n))
    else:
        p("    exceptions: none")
    p("    verdict: %s" % res["verdict"])


# ----------------------------------------------------------------------------
# Claims
# ----------------------------------------------------------------------------

def decision_nodes(players, regime):
    """The mover's move at every decision node (t, cA, cB) of every case of
    `regime`, reachable or not.  The move does not depend on fA, fB (checked
    in run_grid), so fA = fB = 0 is used."""
    nodes = []
    for T in T_GRID:
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                for S in S_GRID:
                    for tie in TIE_RULES:
                        solver = players[(T, Cmax, G, S, regime, tie)]
                        for t in range(1, T + 1):
                            for cA in range(Cmax + 1):
                                for cB in range(Cmax + 1):
                                    c_m, c_t = ((cA, cB) if t % 2 == 1
                                                else (cB, cA))
                                    sab, k = solver.policy(t, (0, cA, 0, cB))
                                    nodes.append({
                                        "T": T, "Cmax": Cmax, "G": G, "S": S,
                                        "tie": tie, "t": t, "sab": sab,
                                        "k": k, "c_mover": c_m, "c_twin": c_t,
                                        "last_turn": ("yes" if t == T
                                                      else "no"),
                                        "cap_binds": ("yes" if 1 + c_m
                                                      > Cmax - c_t
                                                      else "no")})
    return nodes


def claim_rival(rows, players, regime):
    """C1 for RIVAL (or RIVAL_SUM).  Returns a list of results."""
    dom = rows_of(rows, regime)
    zero = lambda r: r["general_total"] == 0
    out = [
        evaluate("a", "%s, G in {0,1}: total general investment = 0"
                 % regime, [r for r in dom if r["G"] < 2], zero),
        evaluate("b", "%s, G = 2: total general investment = 0" % regime,
                 [r for r in dom if r["G"] == 2], zero),
        evaluate("c", "%s, G = 3: total general investment = 0" % regime,
                 [r for r in dom if r["G"] == 3], zero),
        evaluate("d", "%s, every G: k = 0 on every turn before the last "
                 "turn T" % regime, dom,
                 lambda r: all(s["k"] == 0 for s in r["path"][:-1])),
    ]
    # sabotage on the equilibrium path
    onpath = []
    for r in dom:
        if r["S"] != 1:
            continue
        for step, st in zip(r["path"], r["_states"]):
            c_twin = st[3] if step["mover"] == "A" else st[1]
            if c_twin > 0:
                onpath.append({
                    "T": r["T"], "Cmax": r["Cmax"], "G": r["G"],
                    "tie": r["tie"], "sab": step["sab"],
                    "last_turn": "yes" if step["t"] == r["T"] else "no"})
    out.append(evaluate(
        "e", "%s, S = 1, on the equilibrium path: every turn that starts "
        "with twin c > 0 has sab = 1" % regime, onpath,
        lambda d: d["sab"] == 1,
        dims=("last_turn", "G", "tie", "T", "Cmax"), unit="on-path turns"))
    # sabotage at every decision node, reachable or not
    nodes = [d for d in decision_nodes(players, regime)
             if d["S"] == 1 and d["c_twin"] > 0]
    node_dims = ("last_turn", "G", "tie", "cap_binds", "T", "Cmax")
    out.append(evaluate(
        "f", "%s, S = 1, at every decision node (t, cA, cB) with twin "
        "c > 0, reachable or not: sab = 1" % regime, nodes,
        lambda d: d["sab"] == 1, dims=node_dims, unit="nodes"))
    out.append(evaluate(
        "g", "%s, S = 1, same as f but only nodes before the last turn"
        % regime, [d for d in nodes if d["last_turn"] == "no"],
        lambda d: d["sab"] == 1, dims=node_dims, unit="nodes"))
    out.append(evaluate(
        "h", "%s, G in {0,1}: k = 0 at every decision node (t, cA, cB), "
        "reachable or not" % regime,
        [d for d in decision_nodes(players, regime) if d["G"] < 2],
        lambda d: d["k"] == 0,
        dims=("last_turn", "G", "S", "tie", "T", "Cmax"), unit="nodes"))
    return out


def claim_cross(rows, players, regime):
    """C3 for CROSS (or CROSS_SUM)."""
    dom = rows_of(rows, regime)
    zero = lambda r: r["general_total"] == 0
    return [
        evaluate("a", "%s, G in {0,1}: total general investment = 0 "
                 "(every T, Cmax, S, tie rule)" % regime,
                 [r for r in dom if r["G"] < 2], zero),
        evaluate("b", "%s, G = 2: total general investment = 0" % regime,
                 [r for r in dom if r["G"] == 2], zero),
        evaluate("c", "%s, G = 3: total general investment = 0" % regime,
                 [r for r in dom if r["G"] == 3], zero),
        evaluate("d", "%s, G in {0,1}: k = 0 at every decision node "
                 "(t, cA, cB), reachable or not" % regime,
                 [d for d in decision_nodes(players, regime) if d["G"] < 2],
                 lambda d: d["k"] == 0,
                 dims=("last_turn", "G", "S", "tie", "T", "Cmax"),
                 unit="nodes"),
    ]


def claim_collective(rows, regime):
    """C4 for COLLECTIVE (or COLLECTIVE_SUM)."""
    dom = rows_of(rows, regime)
    invest = lambda r: r["general_total"] > 0

    def prefix(r):
        s = switch_turn(r)
        return all(step["k"] > 0 for step in r["path"][:s])

    last_zero = lambda r: r["path"][-1]["k"] == 0
    out = [
        evaluate("a", "%s: total general investment > 0" % regime, dom,
                 invest),
    ]
    cfgs = []
    for Cmax in CMAX_GRID:
        for G in G_GRID:
            for S in S_GRID:
                for tie in TIE_RULES:
                    flags = [invest(r) for r in dom
                             if (r["Cmax"], r["G"], r["S"], r["tie"])
                             == (Cmax, G, S, tie)]      # in T order
                    first = flags.index(True) if True in flags else len(flags)
                    cfgs.append({"Cmax": Cmax, "G": G, "S": S, "tie": tie,
                                 "closed": all(flags[first:])})
    out.append(evaluate(
        "b", "%s: if investment occurs at some T it occurs at every larger "
        "T of the grid (a threshold in T)" % regime, cfgs,
        lambda d: d["closed"], dims=("Cmax", "G", "S", "tie"),
        unit="(Cmax, G, S, tie) configurations"))
    out.append(evaluate(
        "c", "%s, cases with investment: the turns with k > 0 are exactly "
        "turns 1..s for some s (no gap)" % regime,
        [r for r in dom if invest(r)], prefix))
    out.append(evaluate(
        "d", "%s: k = 0 on the last turn T" % regime, dom, last_zero))
    out.append(evaluate(
        "e", "%s: build-then-harvest = investment > 0, turns with k > 0 are "
        "1..s, and k = 0 on the last turn" % regime, dom,
        lambda r: invest(r) and prefix(r) and last_zero(r)))
    out.append(evaluate(
        "f", "%s, cases with investment: the last turn with k > 0 is in "
        "the first half (s <= T/2)" % regime,
        [r for r in dom if invest(r)],
        lambda r: switch_turn(r) <= r["T"] // 2))
    out.append(evaluate(
        "g", "%s, cases with investment: both builder capabilities end at "
        "the cap (cA = cB = Cmax)" % regime,
        [r for r in dom if invest(r)],
        lambda r: r["end"]["cA"] == r["Cmax"] and r["end"]["cB"] == r["Cmax"]))
    at12 = {(r["Cmax"], r["G"], r["tie"]): switch_turn(r)
            for r in dom if r["S"] == 0 and r["T"] == T_GRID[-1]}
    out.append(evaluate(
        "h", "%s, S = 0, T < %d: the switch turn is the same as at T = %d "
        "(same Cmax, G, tie)" % (regime, T_GRID[-1], T_GRID[-1]),
        [r for r in dom if r["S"] == 0 and r["T"] < T_GRID[-1]],
        lambda r: switch_turn(r) == at12[(r["Cmax"], r["G"], r["tie"])],
        dims=("T", "Cmax", "G", "tie")))
    out.append(evaluate(
        "i", "%s, G in {0,1} only: build-then-harvest as defined in e"
        % regime, [r for r in dom if r["G"] < 2],
        lambda r: invest(r) and prefix(r) and last_zero(r)))
    return out


def collective_tables(p, index, regime):
    """Switch-turn table and smallest-T table for C4."""
    for S in S_GRID:
        p("Switch turn = last turn with k > 0 (0 = no investment).  %s, "
          "S = %d." % (regime, S))
        p("Cell: min_general / max_general.")
        body = []
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                line = ["Cmax=%d G=%d" % (Cmax, G)]
                for T in T_GRID:
                    a = switch_turn(index[(T, Cmax, G, S, regime,
                                           "min_general")])
                    b = switch_turn(index[(T, Cmax, G, S, regime,
                                           "max_general")])
                    line.append("%d/%d" % (a, b))
                body.append(line)
        for line in table(["", ] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        p("")
    p("Smallest T of the grid with any general investment.  %s." % regime)
    body = []
    for Cmax in CMAX_GRID:
        for G in G_GRID:
            line = ["Cmax=%d G=%d" % (Cmax, G)]
            for S in S_GRID:
                for tie in TIE_RULES:
                    ts = [T for T in T_GRID
                          if index[(T, Cmax, G, S, regime, tie)]
                          ["general_total"] > 0]
                    line.append(str(ts[0]) if ts else "none")
            body.append(line)
    heads = [""] + ["S=%d %s" % (S, tie) for S in S_GRID for tie in TIE_RULES]
    for line in table(heads, body):
        p("  " + line)
    p("")


# ----------------------------------------------------------------------------
# The report
# ----------------------------------------------------------------------------

class Report:
    """Builds the text report.  Each method writes one section."""

    def __init__(self, rows, index, players, fb, checks, uncapped,
                 other_sab):
        self.rows, self.index, self.players = rows, index, players
        self.fb, self.checks, self.uncapped = fb, checks, uncapped
        self.other_sab = other_sab
        self.out = []
        self.summary = []      # (id, statement, counts, verdict)
        self.c1 = self.c3 = self.c4 = None

    def p(self, line=""):
        self.out.append(line)

    def record(self, claim, res):
        self.summary.append((claim + "." + res["id"], res["statement"],
                             "%d/%d" % (res["n_hold"], res["n"]),
                             res["verdict"]))

    def text(self):
        for step in (self.header, self.section_selfchecks,
                     self.section_first_best, self.section_tie_rules,
                     self.claim_1_rival, self.claim_2_greedy,
                     self.claim_3_cross, self.claim_4_collective,
                     self.claim_5_roundtrip, self.claim_6_efficiency,
                     self.claim_7_symmetry, self.claim_8_summed,
                     self.supplement_no_cap, self.supplement_other_sabotage,
                     self.section_summary,
                     self.appendix_cases):
            step()
        return "\n".join(self.out) + "\n"

    def header(self):
        """Title, grid and reading guide."""
        p = self.p
        n_cases = len(self.rows)
        p("GEMINI CELLS GAME: REPORT")
        p("=" * 78)
        p("Two twins, A and B.  On its turn a cell improves only its twin's "
          "harness.")
        p("A harness has a task capability f and a builder capability c.")
        p("The mover has e = 1 + own c effort units.  A narrow unit adds 2 to "
          "the twin's f.")
        p("A general unit adds 1 to the twin's c (cap Cmax) and G to the "
          "twin's f.")
        p("S = 1 adds a free sabotage option: lower the twin's c by 1 before "
          "the general units.")
        p("")
        p("Grid: T in %s; Cmax in %s; G in %s; S in %s." % (
            fmt_vals(T_GRID), fmt_vals(CMAX_GRID), fmt_vals(G_GRID),
            fmt_vals(S_GRID)))
        p("Regimes: %s." % ", ".join(REGIMES))
        p("Tie rules: %s." % ", ".join(TIE_RULES))
        p("Cases solved: %d = %d T x %d Cmax x %d G x %d S x %d regimes x %d tie "
          "rules.  None dropped." % (
              n_cases, len(T_GRID), len(CMAX_GRID), len(G_GRID), len(S_GRID),
              len(REGIMES), len(TIE_RULES)))
        p("")
        p("HOW TO READ THIS REPORT")
        p("- k-path: one digit per turn, the number of general units placed on "
          "that turn.")
        p("  Turn 1 is the first digit.  A moves on odd turns, B on even turns.")
        p("- General investment of a case: the total of general units on its "
          "path.")
        p("- Each claim is a yes/no statement over a stated domain of cases.  "
          "A case includes")
        p("  its tie rule.  'holds in X of Y' counts cases.  The line 'holds "
          "under both tie")
        p("  rules' counts parameter configurations where both tie rules give "
          "yes.")
        p("- Exceptions are listed exactly, as boxes.  'G=2, tie=max_general "
          "[36]' means all 36")
        p("  cases of the domain with these values, for every value of the "
          "parameters not named.")
        p("- Verdict words.  FOLLOWS: yes in every case of the domain.  FAILS: "
          "yes in no case.")
        p("  DEPENDS on X: yes in some cases; X are the parameters needed to "
          "say which.")
        p("  A statement that DEPENDS on tie does not hold by the 'both tie "
          "rules' standard")
        p("  in the configurations it names.")
        p("- efficiency = (fA + fB at the end) / first-best.  The first-best "
          "excludes sabotage,")
        p("  so with S = 1 an efficiency above 1 is possible.")
        p("- CROSS, RIVAL, COLLECTIVE and the _SUM variants are subgame-perfect "
          "equilibria.")
        p("  GREEDY and ROUNDTRIP are fixed myopic rules, simulated forward.")
        p("")

    def section_selfchecks(self):
        """Checks made while solving the grid."""
        p = self.p
        rows = self.rows
        index = self.index
        checks = self.checks
        p("SECTION 0. SELF-CHECKS DONE DURING THIS RUN")
        p("-" * 78)
        p("Equilibrium cases solved by the literal solver, memo on "
          "(t, fA, cA, fB, cB): %d" % checks["cases_checked"])
        p("Nodes visited from the start state and compared with the reduced "
          "solver: %d" % checks["reachable_nodes"])
        p("Extra nodes (t, cA, cB) with fA = fB = 0, reachable or not, "
          "compared: %d" % checks["offpath_nodes"])
        p("Mismatches in move or in payoffs: 0 (a mismatch aborts the run)")
        p("RIVAL and RIVAL_SUM nodes checked for u_A + u_B = 0: %d, all zero"
          % checks["zero_sum_nodes"])
        n_fb = sum(1 for r in rows_of(rows, "COLLECTIVE", S=0)
                   if r["end_score"] == r["first_best"])
        p("COLLECTIVE, S = 0: end score equals the exhaustive first-best in "
          "%d of %d cases" % (n_fb, len(rows_of(rows, "COLLECTIVE", S=0))))
        n_rt = sum(1 for r in rows_of(rows, "ROUNDTRIP(0)")
                   if r["path"] == index[(r["T"], r["Cmax"], r["G"], r["S"],
                                          "GREEDY", r["tie"])]["path"])
        p("ROUNDTRIP(0) path equals GREEDY path in %d of %d cases"
          % (n_rt, len(rows_of(rows, "ROUNDTRIP(0)"))))
        p("")

    def section_first_best(self):
        """First-best table, efficiency above 1, sabotage on the path."""
        p = self.p
        rows = self.rows
        index = self.index
        fb = self.fb
        n_cases = len(self.rows)
        p("SECTION 1. FIRST-BEST, EFFICIENCY ABOVE 1, SABOTAGE ON THE PATH")
        p("-" * 78)
        p("First-best = largest fA + fB at the end over all move sequences "
          "without sabotage.")
        p("With no general unit at all the end score is 2T.")
        body = []
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                body.append(["Cmax=%d G=%d" % (Cmax, G)]
                            + [fb[(T, Cmax, G)] for T in T_GRID])
        body.append(["no general unit (2T)"] + [2 * T for T in T_GRID])
        for line in table([""] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        p("")
        p("Team optimum when sabotage is allowed (= COLLECTIVE end score with "
          "S = 1).")
        p("A star marks a value above the first-best.")
        body = []
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                line = ["Cmax=%d G=%d" % (Cmax, G)]
                for T in T_GRID:
                    v = index[(T, Cmax, G, 1, "COLLECTIVE",
                               "min_general")]["end_score"]
                    w = index[(T, Cmax, G, 1, "COLLECTIVE",
                               "max_general")]["end_score"]
                    assert v == w
                    line.append("%d%s" % (v, "*" if v > fb[(T, Cmax, G)] else ""))
                body.append(line)
        for line in table([""] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        over = [r for r in rows if r["end_score"] > r["first_best"]]
        outside = [r for r in over if not (r["S"] == 1 and r["G"] == 3)]
        p("")
        p("Cases with efficiency above 1: %d of %d.  Of these, outside "
          "(S = 1, G = 3): %d." % (len(over), n_cases, len(outside)))
        res = evaluate("x", "S = 1, G = 3: end score <= first-best",
                       [r for r in rows if r["S"] == 1 and r["G"] == 3],
                       lambda r: r["end_score"] <= r["first_best"],
                       dims=("regime", "tie", "T", "Cmax"))
        p("Within S = 1, G = 3 (%d cases) the cases above 1 are:" % res["n"])
        for cons, n, _exact in res["boxes"]:
            p("  - %s  [%d]" % (box_text(cons), n))
        p("In these cases a mover lowers the twin's c by 1 and puts it back "
          "with a general unit")
        p("worth G = 3, which beats a narrow unit worth 2 and gets round the "
          "cap.")
        p("")
        p("Sabotage on the path, S = 1: cases with at least one sabotage event, "
          "min_general / max_general,")
        p("each out of 18 (6 T x 3 Cmax).")
        body = []
        for regime in REGIMES:
            line = [regime]
            for G in G_GRID:
                cell = []
                for tie in TIE_RULES:
                    cell.append(str(sum(1 for r in rows_of(rows, regime, G=G,
                                                           S=1, tie=tie)
                                        if r["sabotage_events"] > 0)))
                line.append(" / ".join(cell))
            body.append(line)
        for line in table(["regime"] + ["G=%d" % G for G in G_GRID], body):
            p("  " + line)
        p("")

    def section_tie_rules(self):
        """Where the two tie rules give different paths."""
        p = self.p
        rows = self.rows
        n_cases = len(self.rows)
        p("SECTION 2. TIE-RULE SENSITIVITY")
        p("-" * 78)
        p("For each regime and G: number of (T, Cmax, S) configurations, out of "
          "%d, in which" % (len(T_GRID) * len(CMAX_GRID) * len(S_GRID)))
        p("min_general and max_general give a different path / a different end "
          "score.")
        body = []
        for regime in REGIMES:
            line = [regime]
            for G in G_GRID:
                sel = rows_of(rows, regime, G=G, tie="min_general")
                a = sum(1 for r in sel if r["path_differs_across_tie_rules"])
                b = sum(1 for r in sel if r["score_differs_across_tie_rules"])
                line.append("%d / %d" % (a, b))
            body.append(line)
        for line in table(["regime (path / score)"]
                          + ["G=%d" % G for G in G_GRID], body):
            p("  " + line)
        tot_path = sum(1 for r in rows if r["tie"] == "min_general"
                       and r["path_differs_across_tie_rules"])
        p("")
        p("Configurations (T, Cmax, G, S, regime) whose path differs between "
          "the tie rules: %d of %d." % (tot_path, n_cases // 2))
        p("The flag for every single case is in Appendix A (column tie-diff) "
          "and in game_cases.json.")
        p("")

    def claim_1_rival(self):
        """C1: RIVAL."""
        p = self.p
        rows = self.rows
        players = self.players
        record = self.record
        p("SECTION 3. CLAIMS")
        p("-" * 78)
        p("")
        p("C1. RIVAL: no general investment; with S = 1, sabotage whenever the "
          "twin's c is positive.")
        p("")
        c1 = self.c1 = claim_rival(rows, players, "RIVAL")
        for res in c1:
            print_result(p, res, "C1.")
            record("C1", res)
            p("")
        n_turns = sum(r["T"] for r in rows_of(rows, "RIVAL", S=1))
        n_pos = sum(1 for r in rows_of(rows, "RIVAL", S=1)
                    for step, st in zip(r["path"], r["_states"])
                    if (st[3] if step["mover"] == "A" else st[1]) > 0)
        p("Detail for C1.e.  RIVAL, S = 1: on-path turns in all 144 cases: %d.  "
          "Turns that start" % n_turns)
        p("with twin c > 0: %d.  Sabotage events on the path: %d.  So on the "
          "path the sabotage" % (n_pos, sum(r["sabotage_events"] for r in
                                            rows_of(rows, "RIVAL", S=1))))
        p("statement is never put to the test; C1.f and C1.g test it at every "
          "node off the path.")
        p("Detail for C1.c.  RIVAL, G = 3: turns with k > 0, as (turn - T, "
          "mover, k), over all 72 cases:")
        seen = {}
        for r in rows_of(rows, "RIVAL", G=3):
            for s in r["path"]:
                if s["k"] > 0:
                    key = (s["t"] - r["T"], s["mover"], s["k"])
                    seen[key] = seen.get(key, 0) + 1
        for key in sorted(seen):
            p("  turn T%+d, mover %s, k = %d: %d cases" % (key + (seen[key],)))
        p("Definition used in C1.f and C1.g: cap_binds = yes when the mover has "
          "more effort units")
        p("than free cap room in the twin before any sabotage "
          "(1 + c_mover > Cmax - c_twin).")
        p("Then a sabotage frees room for one more general unit.")
        p("")

    def claim_2_greedy(self):
        """C2: GREEDY."""
        p = self.p
        rows = self.rows
        players = self.players
        record = self.record
        p("C2. GREEDY: general investment is zero iff G < 2.")
        p("")
        gdom = rows_of(rows, "GREEDY")
        zero = lambda r: r["general_total"] == 0
        c2 = [
            evaluate("a", "GREEDY, G in {0,1}: total general investment = 0",
                     [r for r in gdom if r["G"] < 2], zero),
            evaluate("b", "GREEDY, G = 2: total general investment = 0",
                     [r for r in gdom if r["G"] == 2], zero),
            evaluate("c", "GREEDY, G = 3: total general investment > 0",
                     [r for r in gdom if r["G"] == 3], lambda r: not zero(r)),
            evaluate("d", "GREEDY, every G: (total general investment = 0) "
                     "exactly when (G < 2)", gdom,
                     lambda r: zero(r) == (r["G"] < 2)),
        ]
        for res in c2:
            print_result(p, res, "C2.")
            record("C2", res)
            p("")
        # the tie at G = 2
        n_nodes = n_tied = 0
        for r in rows_of(rows, "GREEDY", G=2):
            rule = players[(r["T"], r["Cmax"], 2, r["S"], "GREEDY", r["tie"])]
            for step, st in zip(r["path"], r["_states"]):
                objs = {o for o, _, _ in rule.objective(step["t"], st)}
                n_nodes += 1
                n_tied += (len(objs) == 1)
        p("Detail for C2.b.  GREEDY, G = 2: on-path turns where every legal "
          "move has the same")
        p("objective (a full tie): %d of %d.  So the tie rule alone decides: "
          "min_general gives" % (n_tied, n_nodes))
        p("k = 0 on every turn, max_general gives the largest feasible k on "
          "every turn.")
        body = []
        for G in G_GRID:
            for tie in TIE_RULES:
                sel0 = rows_of(rows, "GREEDY", G=G, tie=tie, S=0)
                sel1 = rows_of(rows, "GREEDY", G=G, tie=tie, S=1)
                body.append([
                    "G=%d %s" % (G, tie),
                    "%d/%d" % (sum(1 for r in sel0 + sel1 if not zero(r)),
                               len(sel0 + sel1)),
                    f4(mean(Fraction(r["end_score"], r["first_best"])
                            for r in sel0)),
                    "%d/%d" % (sum(1 for r in sel1 if r["sabotage_events"] > 0),
                               len(sel1)),
                ])
        p("GREEDY by G and tie rule:")
        for line in table(["", "cases with investment", "mean efficiency S=0",
                           "S=1 cases with sabotage"], body):
            p("  " + line)
        p("")

    def claim_3_cross(self):
        """C3: CROSS."""
        p = self.p
        rows = self.rows
        index = self.index
        players = self.players
        record = self.record
        p("C3. CROSS: no general investment at any horizon when G < 2.")
        p("")
        c3 = self.c3 = claim_cross(rows, players, "CROSS")
        for res in c3:
            print_result(p, res, "C3.")
            record("C3", res)
            p("")
        p("Detail for C3.b and C3.c.  CROSS with S = 0: k-path and efficiency "
          "by tie rule.")
        body = []
        for G in (2, 3):
            for Cmax in CMAX_GRID:
                for T in (2, 4, 8, 12):
                    a = index[(T, Cmax, G, 0, "CROSS", "min_general")]
                    b = index[(T, Cmax, G, 0, "CROSS", "max_general")]
                    body.append(["G=%d Cmax=%d T=%d" % (G, Cmax, T),
                                 k_string(a), a["efficiency_exact"],
                                 k_string(b), b["efficiency_exact"]])
        for line in table(["", "k-path min_general", "eff", "k-path max_general",
                           "eff"], body):
            p("  " + line)
        p("")
        body = []
        for G in G_GRID:
            for tie in TIE_RULES:
                sel = rows_of(rows, "CROSS", G=G, tie=tie, S=0)
                effs = [Fraction(r["end_score"], r["first_best"]) for r in sel]
                body.append(["G=%d %s" % (G, tie), f4(mean(effs)), f4(min(effs)),
                             f4(max(effs))])
        p("CROSS efficiency with S = 0, over T and Cmax (18 cases per line):")
        for line in table(["", "mean", "min", "max"], body):
            p("  " + line)
        p("")

    def claim_4_collective(self):
        """C4: COLLECTIVE."""
        p = self.p
        rows = self.rows
        index = self.index
        record = self.record
        p("C4. COLLECTIVE: investment above a threshold T, early, and none in "
          "the final turns.")
        p("")
        c4 = self.c4 = claim_collective(rows, "COLLECTIVE")
        for res in c4:
            print_result(p, res, "C4.")
            record("C4", res)
            p("")
        collective_tables(p, index, "COLLECTIVE")
        p("COLLECTIVE k-paths with S = 0 (min_general | max_general):")
        body = []
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                line = ["Cmax=%d G=%d" % (Cmax, G)]
                for T in (2, 4, 6, 12):
                    line.append("%s | %s" % (
                        k_string(index[(T, Cmax, G, 0, "COLLECTIVE",
                                        "min_general")]),
                        k_string(index[(T, Cmax, G, 0, "COLLECTIVE",
                                        "max_general")])))
                body.append(line)
        for line in table([""] + ["T=%d" % T for T in (2, 4, 6, 12)], body):
            p("  " + line)
        p("")

    def claim_5_roundtrip(self):
        """C5: ROUNDTRIP(gamma)."""
        p = self.p
        rows = self.rows
        index = self.index
        record = self.record
        p("C5. ROUNDTRIP(gamma): does investment occur, and efficiency relative "
          "to COLLECTIVE.")
        p("")
        p("Per effort unit the ROUNDTRIP objective compares: narrow = 2 against "
          "general = G + gamma * v,")
        p("where v is what one more effort unit is worth to the twin's greedy "
          "next move")
        p("(v = 2, or 3 when G = 3 and the twin can still place a general "
          "unit).")
        p("On the last turn the rule is GREEDY.")
        p("")
        body = []
        c5 = []
        for g in GAMMAS:
            regime = "ROUNDTRIP(%s)" % gamma_label(g)
            for G in G_GRID:
                dom = rows_of(rows, regime, G=G)
                res = evaluate("gamma=%s,G=%d" % (gamma_label(g), G),
                               "%s, G = %d: total general investment > 0"
                               % (regime, G), dom,
                               lambda r: r["general_total"] > 0)
                c5.append(res)
                record("C5", res)
                rel = {}
                for S in S_GRID:
                    rel[S] = [Fraction(r["end_score"],
                                       index[(r["T"], r["Cmax"], G, S,
                                              "COLLECTIVE", r["tie"])]
                                       ["end_score"])
                              for r in dom if r["S"] == S]
                cnt = {tie: sum(1 for r in dom if r["tie"] == tie
                                and r["general_total"] > 0)
                       for tie in TIE_RULES}
                if res["n_hold"] == res["n"]:
                    word = "always"
                elif res["n_hold"] == 0:
                    word = "never"
                else:
                    word = res["verdict"].split(" (")[0].replace(
                        "DEPENDS on ", "depends on ")
                body.append([
                    "gamma=%s G=%d" % (gamma_label(g), G),
                    "%d/36" % cnt["min_general"], "%d/36" % cnt["max_general"],
                    word,
                    "%s [%s, %s]" % (f4(mean(rel[0])), f4(min(rel[0])),
                                     f4(max(rel[0]))),
                    "%s [%s, %s]" % (f4(mean(rel[1])), f4(min(rel[1])),
                                     f4(max(rel[1]))),
                ])
        p("Columns: cases with investment under each tie rule (36 = 6 T x 3 "
          "Cmax x 2 S each);")
        p("whether investment occurs; end score / COLLECTIVE end score as mean "
          "[min, max], for S = 0 and S = 1.")
        for line in table(["", "invest min_gen", "invest max_gen", "investment",
                           "rel. eff S=0", "rel. eff S=1"], body):
            p("  " + line)
        p("")
        p("ROUNDTRIP end score / COLLECTIVE end score by T (S = 0, mean over "
          "Cmax; min_general | max_general):")
        body = []
        for g in GAMMAS:
            regime = "ROUNDTRIP(%s)" % gamma_label(g)
            for G in G_GRID:
                line = ["gamma=%s G=%d" % (gamma_label(g), G)]
                for T in T_GRID:
                    cell = []
                    for tie in TIE_RULES:
                        cell.append("%.3f" % float(mean(
                            Fraction(index[(T, Cmax, G, 0, regime, tie)]
                                     ["end_score"],
                                     index[(T, Cmax, G, 0, "COLLECTIVE", tie)]
                                     ["end_score"]) for Cmax in CMAX_GRID)))
                    line.append(cell[0] if cell[0] == cell[1]
                                else "%s|%s" % tuple(cell))
                body.append(line)
        for line in table([""] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        p("")
        for res in c5:
            if res["boxes"] and res["n_hold"]:
                print_result(p, res, "C5.")
                p("")
        rt_rows = [r for r in rows if r["regime"].startswith("ROUNDTRIP")]

        def threshold_rule(r):
            lhs = r["G"] + 2 * Fraction(r["gamma"])
            want = lhs > 2 or (lhs == 2 and r["tie"] == "max_general")
            return (r["general_total"] > 0) == want

        res = evaluate(
            "threshold", "ROUNDTRIP, all gamma and G: investment occurs "
            "exactly when G + 2*gamma > 2, or G + 2*gamma = 2 and the tie "
            "rule is max_general", rt_rows, threshold_rule,
            dims=("regime", "G", "tie", "T", "Cmax", "S"))
        print_result(p, res, "C5.")
        record("C5", res)
        p("")
        res = evaluate(
            "efficient", "ROUNDTRIP, cases with investment: end score = "
            "COLLECTIVE end score (same T, Cmax, G, S, tie)",
            [r for r in rt_rows if r["general_total"] > 0],
            lambda r: r["end_score"] == index[
                (r["T"], r["Cmax"], r["G"], r["S"], "COLLECTIVE",
                 r["tie"])]["end_score"],
            dims=("regime", "G", "tie", "T", "Cmax", "S"))
        print_result(p, res, "C5.")
        record("C5", res)
        p("")

    def claim_6_efficiency(self):
        """C6: efficiency ranking and COLLECTIVE / CROSS."""
        p = self.p
        rows = self.rows
        index = self.index
        record = self.record
        p("C6. Efficiency ranking and the price of plain cross-scoring.")
        p("")
        p("Mean efficiency per regime, S = 0 (144 cases per regime = 6 T x 3 "
          "Cmax x 4 G x 2 tie rules):")
        body = []
        for regime in REGIMES:
            sel = rows_of(rows, regime, S=0)
            effs = [Fraction(r["end_score"], r["first_best"]) for r in sel]
            by_tie = [mean(Fraction(r["end_score"], r["first_best"])
                           for r in sel if r["tie"] == tie) for tie in TIE_RULES]
            low = mean(Fraction(r["end_score"], r["first_best"])
                       for r in sel if r["G"] < 2)
            body.append((mean(effs), [regime, f4(mean(effs)), f4(min(effs)),
                                      f4(max(effs)), f4(by_tie[0]),
                                      f4(by_tie[1]), f4(low)]))
        body.sort(key=lambda x: (-x[0], REGIMES.index(x[1][0])))
        for line in table(["regime", "mean", "min", "max", "mean min_gen",
                           "mean max_gen", "mean G<2"],
                          [b for _, b in body]):
            p("  " + line)
        p("")
        p("Same with S = 1 (the first-best still excludes sabotage):")
        body = []
        for regime in REGIMES:
            sel = rows_of(rows, regime, S=1)
            effs = [Fraction(r["end_score"], r["first_best"]) for r in sel]
            by_tie = [mean(Fraction(r["end_score"], r["first_best"])
                           for r in sel if r["tie"] == tie) for tie in TIE_RULES]
            low = mean(Fraction(r["end_score"], r["first_best"])
                       for r in sel if r["G"] < 2)
            body.append((mean(effs), [regime, f4(mean(effs)), f4(min(effs)),
                                      f4(max(effs)), f4(by_tie[0]),
                                      f4(by_tie[1]), f4(low)]))
        body.sort(key=lambda x: (-x[0], REGIMES.index(x[1][0])))
        for line in table(["regime", "mean", "min", "max", "mean min_gen",
                           "mean max_gen", "mean G<2"],
                          [b for _, b in body]):
            p("  " + line)
        p("")
        p("Price of plain cross-scoring: COLLECTIVE end score / CROSS end "
          "score, S = 0.")
        for tie in TIE_RULES:
            p("Tie rule %s:" % tie)
            body = []
            for T in T_GRID:
                line = ["T=%d" % T]
                vals = []
                for Cmax in CMAX_GRID:
                    for G in G_GRID:
                        v = Fraction(
                            index[(T, Cmax, G, 0, "COLLECTIVE", tie)]["end_score"],
                            index[(T, Cmax, G, 0, "CROSS", tie)]["end_score"])
                        vals.append(v)
                        line.append("%.3f" % float(v))
                line.append("%.3f" % float(mean(vals)))
                body.append(line)
            heads = [""] + ["C%dG%d" % (Cmax, G) for Cmax in CMAX_GRID
                            for G in G_GRID] + ["mean"]
            for line in table(heads, body):
                p("  " + line)
            p("")
        p("Same ratio for G < 2 only (there both tie rules give the same CROSS "
          "path), mean over Cmax and G:")
        body = []
        for T in T_GRID:
            vals = [Fraction(index[(T, Cmax, G, 0, "COLLECTIVE", tie)]
                             ["end_score"],
                             index[(T, Cmax, G, 0, "CROSS", tie)]["end_score"])
                    for Cmax in CMAX_GRID for G in (0, 1) for tie in TIE_RULES]
            body.append(["T=%d" % T, "%.4f" % float(mean(vals)),
                         "%.4f" % float(min(vals)), "%.4f" % float(max(vals))])
        for line in table(["", "mean", "min", "max"], body):
            p("  " + line)
        low = [r for r in rows_of(rows, "CROSS") if r["G"] < 2]
        same = sum(1 for r in low
                   if all(index[(r["T"], r["Cmax"], r["G"], r["S"], other,
                                 r["tie"])]["path"] == r["path"]
                          for other in ("RIVAL", "GREEDY", "CROSS_SUM",
                                        "RIVAL_SUM")))
        plain = sum(1 for r in low if r["general_total"] == 0
                    and r["sabotage_events"] == 0
                    and r["end_score"] == 2 * r["T"])
        p("")
        p("G in {0,1}: CROSS, RIVAL, GREEDY, CROSS_SUM and RIVAL_SUM have the "
          "same path in %d of %d" % (same, len(low)))
        p("(T, Cmax, G, S, tie) cases.  That path has no general unit, no "
          "sabotage and end score 2T")
        p("in %d of %d cases." % (plain, len(low)))
        c6 = evaluate(
            "a", "S = 0: COLLECTIVE end score >= end score of every other "
            "regime in the same (T, Cmax, G, tie)",
            [r for r in rows if r["S"] == 0],
            lambda r: r["end_score"] <= index[(r["T"], r["Cmax"], r["G"], 0,
                                               "COLLECTIVE", r["tie"])]
            ["end_score"], dims=("regime", "G", "tie", "T", "Cmax"))
        p("")
        print_result(p, c6, "C6.")
        record("C6", c6)
        c6b = evaluate(
            "b", "S = 0, G in {0,1}: COLLECTIVE end score > CROSS end score",
            [r for r in rows_of(rows, "CROSS", S=0) if r["G"] < 2],
            lambda r: r["end_score"] < index[(r["T"], r["Cmax"], r["G"], 0,
                                              "COLLECTIVE", r["tie"])]
            ["end_score"], dims=("T", "Cmax", "G", "tie"))
        p("")
        print_result(p, c6b, "C6.")
        record("C6", c6b)
        p("")

    def claim_7_symmetry(self):
        """C7: symmetry of the end state under COLLECTIVE."""
        p = self.p
        rows = self.rows
        record = self.record
        p("C7. Symmetry breaking under COLLECTIVE.")
        p("")
        cdom = rows_of(rows, "COLLECTIVE")
        c7 = [
            evaluate("a", "COLLECTIVE: the twins end equal (fA = fB and "
                     "cA = cB)", cdom,
                     lambda r: r["end"]["fA"] == r["end"]["fB"]
                     and r["end"]["cA"] == r["end"]["cB"]),
            evaluate("b", "COLLECTIVE, cases with fA != fB at the end: A's "
                     "harness is ahead (fA > fB)",
                     [r for r in cdom if r["end"]["fA"] != r["end"]["fB"]],
                     lambda r: r["end"]["fA"] > r["end"]["fB"]),
            evaluate("c", "COLLECTIVE, cases with cA != cB at the end: B's "
                     "builder capability is ahead (cB > cA)",
                     [r for r in cdom if r["end"]["cA"] != r["end"]["cB"]],
                     lambda r: r["end"]["cB"] > r["end"]["cA"]),
        ]
        body = []
        for S in S_GRID:
            for tie in TIE_RULES:
                sel = [r for r in cdom if r["S"] == S and r["tie"] == tie]
                e = [r["end"] for r in sel]
                body.append([
                    "S=%d %s" % (S, tie), len(sel),
                    sum(1 for x in e if x["cA"] != x["cB"]),
                    sum(1 for x in e if x["fA"] != x["fB"]),
                    sum(1 for x in e if x["cA"] != x["cB"]
                        or x["fA"] != x["fB"]),
                    sum(1 for x in e if x["fA"] > x["fB"]),
                    sum(1 for x in e if x["fA"] < x["fB"]),
                    sum(1 for x in e if x["cA"] > x["cB"]),
                    sum(1 for x in e if x["cA"] < x["cB"]),
                ])
        e = [r["end"] for r in cdom]
        body.append(["all", len(cdom),
                     sum(1 for x in e if x["cA"] != x["cB"]),
                     sum(1 for x in e if x["fA"] != x["fB"]),
                     sum(1 for x in e if x["cA"] != x["cB"]
                         or x["fA"] != x["fB"]),
                     sum(1 for x in e if x["fA"] > x["fB"]),
                     sum(1 for x in e if x["fA"] < x["fB"]),
                     sum(1 for x in e if x["cA"] > x["cB"]),
                     sum(1 for x in e if x["cA"] < x["cB"])])
        p("End states under COLLECTIVE.  fA is A's task capability (built by "
          "B, who moves last).")
        for line in table(["", "cases", "cA!=cB", "fA!=fB", "either", "fA>fB",
                           "fA<fB", "cA>cB", "cA<cB"], body):
            p("  " + line)
        p("")
        for res in c7:
            print_result(p, res, "C7.")
            record("C7", res)
            p("")
        diffs = {}
        for r in cdom:
            d = r["end"]["fA"] - r["end"]["fB"]
            diffs.setdefault(r["T"], []).append(d)
        body = [["T=%d" % T, min(v), max(v), f4(mean(Fraction(x) for x in v))]
                for T, v in sorted(diffs.items())]
        p("fA - fB at the end under COLLECTIVE, by T (all Cmax, G, S, tie):")
        for line in table(["", "min", "max", "mean"], body):
            p("  " + line)
        p("")

    def claim_8_summed(self):
        """C8: the summed-payoff variants."""
        c1, c3, c4 = self.c1, self.c3, self.c4
        p = self.p
        rows = self.rows
        index = self.index
        players = self.players
        summary = self.summary
        p("C8. The _SUM variants: do the verdicts of C1, C3, C4 change?")
        p("")
        p("C2 concerns GREEDY, which has no summed variant.  It is not "
          "affected.")
        p("")
        pairs = (
            [("C1", a, b) for a, b in zip(c1, claim_rival(rows, players,
                                                          "RIVAL_SUM"))]
            + [("C3", a, b) for a, b in zip(c3, claim_cross(rows, players,
                                                          "CROSS_SUM"))]
            + [("C4", a, b) for a, b in zip(c4, claim_collective(
                rows, "COLLECTIVE_SUM"))])
        body = []
        changed = []
        for claim, a, b in pairs:
            word_a, word_b = a["kind"].split(" ")[0], b["kind"].split(" ")[0]
            same_set = ((a["n"], a["n_hold"]) == (b["n"], b["n_hold"])
                        and a["boxes"] == b["boxes"])
            if word_a != word_b:
                flag = "VERDICT CHANGES"
            elif same_set:
                flag = "no"
            elif a["boxes"] == b["boxes"]:
                flag = "same verdict, domain size differs"
            else:
                flag = "same verdict word, other exceptions"
            body.append(["%s.%s" % (claim, a["id"]),
                         "%d/%d" % (a["n_hold"], a["n"]), a["kind"],
                         "%d/%d" % (b["n_hold"], b["n"]), b["kind"], flag])
            if not same_set:
                changed.append((claim, a, b))
            summary.append(("C8/" + claim + "." + a["id"], b["statement"],
                            "%d/%d" % (b["n_hold"], b["n"]),
                            b["verdict"] + "  [change vs end scoring: %s]" % flag))
        for line in table(["sub-claim", "END holds", "END verdict", "SUM holds",
                           "SUM verdict", "change"], body):
            p("  " + line)
        p("")
        p("Sub-claims whose result differs under summed payoffs, in full:")
        p("")
        for claim, a, b in changed:
            print_result(p, b, "C8/" + claim + ".")
            p("")
        collective_tables(p, index, "COLLECTIVE_SUM")
        body = []
        for base in BASES:
            n = sum(1 for r in rows_of(rows, base)
                    if r["path"] != index[(r["T"], r["Cmax"], r["G"], r["S"],
                                           base + "_SUM", r["tie"])]["path"])
            sel = rows_of(rows, base + "_SUM", S=0)
            body.append([base + "_SUM", "%d/288" % n,
                         f4(mean(Fraction(r["end_score"], r["first_best"])
                                 for r in sel)),
                         f4(mean(Fraction(r["end_score"], r["first_best"])
                                 for r in rows_of(rows, base, S=0)))])
        p("Cases whose path differs from the end-scored regime, and mean "
          "efficiency (S = 0):")
        for line in table(["", "path differs", "mean eff SUM", "mean eff END"],
                          body):
            p("  " + line)
        p("")

    def supplement_no_cap(self):
        """Supplement outside the grid: a cap that never binds."""
        p = self.p
        uncapped = self.uncapped
        p("SUPPLEMENT U. NO CAP (OUTSIDE THE REQUESTED GRID)")
        p("-" * 78)
        p("The grid has Cmax <= 3.  C4.g and C4.h show that in the grid the "
          "build phase of")
        p("COLLECTIVE mostly ends because the caps are reached.  This "
          "supplement repeats COLLECTIVE")
        p("and CROSS with S = 0 and a cap that never binds (Cmax = %d).  "
          "Reduced solver only." % NO_CAP)
        p("These %d cases are not in game_cases.json and not in any count "
          "above." % len(uncapped))
        p("Largest c reached in any of them: %d."
          % max(max(u["end"][1], u["end"][3]) for u in uncapped.values()))
        p("")
        p("Switch turn (last turn with k > 0; 0 = none), min_general / "
          "max_general:")
        body = []
        for regime in UNCAPPED_REGIMES:
            for G in G_GRID:
                line = ["%s G=%d" % (regime, G)]
                for T in T_GRID:
                    line.append("%d/%d" % tuple(
                        uncapped[(T, G, regime, tie)]["switch"]
                        for tie in TIE_RULES))
                body.append(line)
        for line in table([""] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        p("")
        p("End score fA + fB, min_general / max_general:")
        body = []
        for regime in UNCAPPED_REGIMES:
            for G in G_GRID:
                line = ["%s G=%d" % (regime, G)]
                for T in T_GRID:
                    a, b = (uncapped[(T, G, regime, tie)]["score"]
                            for tie in TIE_RULES)
                    line.append(str(a) if a == b else "%d/%d" % (a, b))
                body.append(line)
        for line in table([""] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        p("")
        p("k per turn at T = %d:" % T_GRID[-1])
        for regime in UNCAPPED_REGIMES:
            for G in G_GRID:
                for tie in TIE_RULES:
                    u = uncapped[(T_GRID[-1], G, regime, tie)]
                    p("  %-10s G=%d %-11s k = %s" % (
                        regime, G, tie, ",".join(str(k) for k in u["ks"])))
        p("")
        p("COLLECTIVE end score / CROSS end score without a cap:")
        body = []
        for G in G_GRID:
            for tie in TIE_RULES:
                line = ["G=%d %s" % (G, tie)]
                for T in T_GRID:
                    line.append("%.3f" % float(Fraction(
                        uncapped[(T, G, "COLLECTIVE", tie)]["score"],
                        uncapped[(T, G, "CROSS", tie)]["score"])))
                body.append(line)
        for line in table([""] + ["T=%d" % T for T in T_GRID], body):
            p("  " + line)
        p("")

    def supplement_other_sabotage(self):
        """Supplement outside the grid: the other reading of sabotage."""
        p = self.p
        index = self.index
        s2_rows, _s2_index, s2_players = self.other_sab
        p("SUPPLEMENT V. THE OTHER READING OF THE SABOTAGE RULE (OUTSIDE THE "
          "REQUESTED GRID)")
        p("-" * 78)
        p("In the model (S = 1) the sabotage is applied first and the cap is "
          "checked afterwards,")
        p("so a sabotage frees room for one more general unit in the same "
          "move.  Under the other")
        p("reading (S = 2 in the code) the room is counted before the "
          "sabotage: k <= min(e, Cmax - c_j).")
        p("All regimes, both tie rules, reduced solver only.  These %d cases "
          "are not in" % len(s2_rows))
        p("game_cases.json and not in any count above.")
        p("")
        p("Cases with efficiency above 1 under S = 2: %d of %d."
          % (sum(1 for r in s2_rows if r["end_score"] > r["first_best"]),
             len(s2_rows)))
        p("")
        p("Sabotage on the path, S = 2: cases with at least one sabotage "
          "event, min_general / max_general,")
        p("each out of 18 (6 T x 3 Cmax).")
        body = []
        for regime in REGIMES:
            line = [regime]
            for G in G_GRID:
                cell = []
                for tie in TIE_RULES:
                    cell.append(str(sum(
                        1 for r in s2_rows
                        if (r["regime"], r["G"], r["tie"]) == (regime, G, tie)
                        and r["sabotage_events"] > 0)))
                line.append(" / ".join(cell))
            body.append(line)
        for line in table(["regime"] + ["G=%d" % G for G in G_GRID], body):
            p("  " + line)
        p("")
        p("Cases whose end score differs from the same case with S = 0 / "
          "with S = 1, out of 36 (6 T x 3 Cmax x 2 tie rules):")
        body = []
        for regime in REGIMES:
            line = [regime]
            for G in G_GRID:
                sel = [r for r in s2_rows
                       if (r["regime"], r["G"]) == (regime, G)]
                d0 = sum(1 for r in sel if r["end_score"] != index[
                    (r["T"], r["Cmax"], G, 0, regime, r["tie"])]["end_score"])
                d1 = sum(1 for r in sel if r["end_score"] != index[
                    (r["T"], r["Cmax"], G, 1, regime, r["tie"])]["end_score"])
                line.append("%d / %d" % (d0, d1))
            body.append(line)
        for line in table(["regime (vs S=0 / vs S=1)"]
                          + ["G=%d" % G for G in G_GRID], body):
            p("  " + line)
        p("")
        p("Mean efficiency at G = 3 (18 cases per cell = 6 T x 3 Cmax), "
          "S = 0 / S = 1 / S = 2:")
        body = []
        for regime in ("CROSS", "CROSS_SUM", "COLLECTIVE", "GREEDY"):
            line = [regime]
            for tie in TIE_RULES:
                cell = []
                for S in (0, 1):
                    cell.append(f4(mean(
                        Fraction(r["end_score"], r["first_best"])
                        for r in rows_of(self.rows, regime, G=3, S=S,
                                         tie=tie))))
                cell.append(f4(mean(
                    Fraction(r["end_score"], r["first_best"]) for r in s2_rows
                    if (r["regime"], r["G"], r["tie"]) == (regime, 3, tie))))
                line.append(" / ".join(cell))
            body.append(line)
        for line in table(["regime"] + list(TIE_RULES), body):
            p("  " + line)
        p("")
        for regime in ("RIVAL", "RIVAL_SUM"):
            n = hold = n_last = hold_last = 0
            for (T, Cmax, G, reg, tie), solver in s2_players.items():
                if reg != regime:
                    continue
                for t in range(1, T + 1):
                    for cA in range(Cmax + 1):
                        for cB in range(Cmax + 1):
                            c_t = cB if t % 2 == 1 else cA
                            if c_t == 0:
                                continue
                            sab, _k = solver.policy(t, (0, cA, 0, cB))
                            if t == T:
                                n_last += 1
                                hold_last += sab
                            else:
                                n += 1
                                hold += sab
            p("%s, S = 2, decision nodes with twin c > 0: sab = 1 at %d of %d "
              "nodes before the last turn" % (regime, hold, n))
            p("  and at %d of %d nodes on the last turn." % (hold_last, n_last))
        on_path = sum(r["sabotage_events"] for r in s2_rows
                      if r["regime"] in ("RIVAL", "RIVAL_SUM"))
        p("RIVAL and RIVAL_SUM, S = 2: sabotage events on the path: %d."
          % on_path)
        p("")

    def section_summary(self):
        """One line per sub-claim."""
        p = self.p
        summary = self.summary
        p("SECTION 4. VERDICT SUMMARY")
        p("-" * 78)
        p("One line per sub-claim.  Counts are cases (or the unit named in the "
          "section above).")
        p("")
        for cid, statement, counts, verdict in summary:
            p("%-20s %9s  %s" % (cid, counts, verdict))
            p("%-20s %9s    %s" % ("", "", statement))
        p("")

    def appendix_cases(self):
        """One line per case."""
        p = self.p
        rows = self.rows
        p("APPENDIX A. EVERY CASE")
        p("-" * 78)
        p("Columns: parameters; k = general units per turn; sab = sabotage per "
          "turn; e = effort per turn;")
        p("gA, gB = general units placed by A and by B; sb = sabotage events; "
          "end = fA,cA,fB,cB;")
        p("score = fA + fB; FB = first-best; eff = score / FB; tie-diff = Y if "
          "the path differs")
        p("between the two tie rules.")
        p("")
        for r in rows:
            e = r["end"]
            p("T=%-2d Cmax=%d G=%d S=%d %-14s %-11s k=%-12s sab=%-12s e=%-12s "
              "gA=%d gB=%d sb=%-2d end=%d,%d,%d,%d score=%d FB=%d eff=%s=%.4f "
              "tie-diff=%s" % (
                  r["T"], r["Cmax"], r["G"], r["S"], r["regime"], r["tie"],
                  k_string(r), sab_string(r), e_string(r), r["general_A"],
                  r["general_B"], r["sabotage_events"], e["fA"], e["cA"],
                  e["fB"], e["cB"], r["end_score"], r["first_best"],
                  r["efficiency_exact"], r["efficiency"],
                  "Y" if r["path_differs_across_tie_rules"] else "N"))
        p("")
        p("END OF REPORT")


def build_report(rows, index, players, fb, checks, uncapped, other_sab):
    return Report(rows, index, players, fb, checks, uncapped,
                  other_sab).text()


NO_CAP = 10 ** 6                       # a cap no path in the grid can reach
UNCAPPED_REGIMES = ("COLLECTIVE", "CROSS")


def run_uncapped():
    """Supplement outside the requested grid: S = 0 and no effective cap.
    Solved with the reduced solver.  Returns {(T, G, regime, tie): info}."""
    out = {}
    for T in T_GRID:
        for G in G_GRID:
            for regime in UNCAPPED_REGIMES:
                for tie in TIE_RULES:
                    player = make_player(T, NO_CAP, G, 0, regime, tie,
                                         literal=False)
                    path, states = play(player)
                    end = states[-1]
                    assert max(end[1], end[3]) < NO_CAP
                    ks = [k for (_, _, _, k, _) in path]
                    out[(T, G, regime, tie)] = {
                        "ks": ks, "end": end, "score": end[0] + end[2],
                        "switch": max([t for (t, _, _, k, _) in path
                                       if k > 0] or [0])}
    return out


OTHER_SABOTAGE = 2                     # the S value of the other reading


def run_other_sabotage(fb):
    """Supplement outside the requested grid: S = 2 (see legal_moves), all
    regimes, reduced solver.  Returns (rows, index, players)."""
    rows, index, players = [], {}, {}
    for T in T_GRID:
        for Cmax in CMAX_GRID:
            for G in G_GRID:
                for regime in REGIMES:
                    for tie in TIE_RULES:
                        row, player = solve_case(
                            T, Cmax, G, OTHER_SABOTAGE, regime, tie,
                            fb[(T, Cmax, G)], literal=False)
                        key = (T, Cmax, G, regime, tie)
                        rows.append(row)
                        index[key] = row
                        players[key] = player
    return rows, index, players


def write_json(rows, fb, path):
    """One row per solved case, one row per line."""
    meta = {
        "model": "gemini-cells-game",
        "grid": {"T": list(T_GRID), "Cmax": list(CMAX_GRID),
                 "G": list(G_GRID), "S": list(S_GRID),
                 "regimes": list(REGIMES), "tie_rules": list(TIE_RULES)},
        "n_cases": len(rows),
        "fields": {
            "path": "per turn: t, mover, sab (0/1), k (general units), "
                    "e (effort units)",
            "gamma": "ROUNDTRIP weight as a fraction string, else null",
            "general_A": "general units placed by A (into B's harness)",
            "general_B": "general units placed by B (into A's harness)",
            "general_total": "general_A + general_B",
            "sabotage_A": "turns on which A sabotaged",
            "sabotage_B": "turns on which B sabotaged",
            "sabotage_events": "number of turns with sab = 1",
            "end": "state after turn T",
            "end_score": "fA + fB at the end",
            "first_best": "max fA + fB over all move sequences, no sabotage",
            "efficiency": "end_score / first_best (float, 6 places)",
            "efficiency_exact": "the same as an exact fraction",
            "payoff_A": "equilibrium payoff of A (null for myopic rules)",
            "payoff_B": "equilibrium payoff of B (null for myopic rules)",
            "path_differs_across_tie_rules": "true if min_general and "
                                             "max_general give other paths",
            "end_differs_across_tie_rules": "the same for the end state",
            "score_differs_across_tie_rules": "the same for end_score",
        },
        "first_best": [{"T": T, "Cmax": Cmax, "G": G, "value": v}
                       for (T, Cmax, G), v in sorted(fb.items())],
    }
    with open(path, "w") as fh:
        fh.write('{"meta": %s,\n "cases": [\n' % json.dumps(meta))
        lines = []
        for r in rows:
            clean = {k: v for k, v in r.items() if not k.startswith("_")}
            lines.append("  " + json.dumps(clean))
        fh.write(",\n".join(lines))
        fh.write("\n ]\n}\n")


def main():
    t0 = time.perf_counter()
    rows, index, players, fb, checks = run_grid(crosscheck=True)
    t1 = time.perf_counter()
    uncapped = run_uncapped()
    other_sab = run_other_sabotage(fb)
    t1b = time.perf_counter()
    report = build_report(rows, index, players, fb, checks, uncapped,
                          other_sab)
    sys.stdout.write(report)
    here = os.path.dirname(os.path.abspath(__file__))
    write_json(rows, fb, os.path.join(here, "game_cases.json"))
    t2 = time.perf_counter()
    sys.stderr.write("grid + cross-check: %.1f s; supplements: %.1f s; "
                     "report + json: %.1f s; total: %.1f s; cases: %d\n"
                     % (t1 - t0, t1b - t1, t2 - t1b, t2 - t0, len(rows)))


if __name__ == "__main__":
    main()
