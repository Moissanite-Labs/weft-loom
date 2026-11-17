#!/usr/bin/env python3
"""A second solver for the twin-cell game, written by the lead without reading game.py.

It re-solves every case in game_cases.json (all regimes, both tie rules, with and without
sabotage) from the model as README.md states it, and compares the end state and the
per-turn moves. Run `python3 game.py > game.out` first; that writes game_cases.json.

    python3 recheck.py > recheck.out
"""

import json
import sys
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMINAL = {"CROSS", "RIVAL", "COLLECTIVE"}
SUMMED = {"CROSS_SUM": "CROSS", "RIVAL_SUM": "RIVAL", "COLLECTIVE_SUM": "COLLECTIVE"}


def solve(T, Cmax, G, S, regime, tie, gamma=Fraction(0)):
    """Return (end state, [(sab, k) per turn]). State is (fA, cA, fB, cB)."""

    def moves(state, t):
        fA, cA, fB, cB = state
        mover_c, twin_f, twin_c = (cA, fB, cB) if t % 2 == 1 else (cB, fA, cA)
        e = 1 + mover_c
        for sab in ((0, 1) if (S and twin_c > 0) else (0,)):
            c0 = twin_c - sab
            for k in range(0, min(e, Cmax - c0) + 1):
                f1, c1 = twin_f + 2 * (e - k) + G * k, c0 + k
                yield (sab, k), ((fA, cA, f1, c1) if t % 2 == 1 else (f1, c1, fB, cB))

    def stage(state, kind):
        fA, _, fB, _ = state
        return {"CROSS": (fB, fA), "RIVAL": (fB - fA, fA - fB), "COLLECTIVE": (fA + fB, fA + fB)}[kind]

    def pick(cands):
        """cands: (value, (sab, k), next state). Best value, then the tie rule, then no sabotage."""
        best = max(c[0] for c in cands)
        ties = [c for c in cands if c[0] == best]
        if tie == "min_general":
            return min(ties, key=lambda c: (c[1][1], c[1][0]))
        return min(ties, key=lambda c: (-c[1][1], c[1][0]))

    def greedy(state, t):
        me = t % 2
        return pick([((n[2] - state[2]) if me == 1 else (n[0] - state[0]), m, n) for m, n in moves(state, t)])

    if regime in TERMINAL or regime in SUMMED:
        kind, summed = SUMMED.get(regime, regime), regime in SUMMED

        @lru_cache(None)
        def val(state, t):
            if t > T:
                return ((0, 0) if summed else stage(state, kind)), ()
            me = 0 if t % 2 == 1 else 1
            cands = []
            for m, n in moves(state, t):
                v, path = val(n, t + 1)
                if summed:
                    s = stage(n, kind)
                    v = (v[0] + s[0], v[1] + s[1])
                cands.append((v[me], m, n, v, path))
            c = pick([(x[0], x[1], x[2]) for x in cands])
            full = next(x for x in cands if x[1] == c[1])
            return full[3], (c[1],) + full[4]

        _, path = val((0, 0, 0, 0), 1)
        st = (0, 0, 0, 0)
        for t, m in enumerate(path, 1):
            st = next(n for mm, n in moves(st, t) if mm == m)
        return st, list(path)

    st, path = (0, 0, 0, 0), []
    for t in range(1, T + 1):
        me = t % 2
        if regime == "GREEDY" or t == T:
            c = greedy(st, t)
        else:
            cands = []
            for m, n in moves(st, t):
                own = (n[2] - st[2]) if me == 1 else (n[0] - st[0])
                reply = greedy(n, t + 1)[2]
                back = (reply[0] - n[0]) if me == 1 else (reply[2] - n[2])
                cands.append((own + gamma * back, m, n))
            c = pick(cands)
        path.append(c[1])
        st = c[2]
    return st, path


def main() -> int:
    src = HERE / "game_cases.json"
    if not src.exists():
        print("game_cases.json is missing: run `python3 game.py > game.out` first")
        return 2
    raw = src.read_text()
    try:
        data = json.loads(raw)
        rows = data["cases"] if isinstance(data, dict) else data
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    rows = [r for r in rows if isinstance(r, dict) and "regime" in r]
    per, bad = {}, 0
    for r in rows:
        reg, g = r["regime"], Fraction(0)
        if reg.startswith("ROUNDTRIP"):
            reg, g = "ROUNDTRIP", Fraction(r["gamma"])
        st, path = solve(r["T"], r["Cmax"], r["G"], r["S"], reg, r["tie"], g)
        end = r["end"]
        theirs = (end["fA"], end["cA"], end["fB"], end["cB"]) if isinstance(end, dict) else tuple(end)
        their_path = [((p["sab"], p["k"]) if isinstance(p, dict) else (p[2], p[3])) for p in r["path"]]
        ok = tuple(st) == tuple(theirs) and [tuple(m) for m in path] == [tuple(m) for m in their_path]
        n, m = per.get(r["regime"], (0, 0))
        per[r["regime"]] = (n + 1, m + (0 if ok else 1))
        if not ok:
            bad += 1
            if bad <= 10:
                print("MISMATCH", r["regime"], "T", r["T"], "Cmax", r["Cmax"], "G", r["G"], "S", r["S"],
                      r["tie"], "mine", st, path, "theirs", theirs, their_path)
    print(f"{'regime':16s} cases  mismatches")
    for reg in sorted(per):
        print(f"{reg:16s} {per[reg][0]:5d}  {per[reg][1]}")
    print(f"total {len(rows)} cases, {bad} mismatches")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
