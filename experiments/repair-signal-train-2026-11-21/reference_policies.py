"""Deterministic policies that play the model in dry runs.

Each takes a View (public constraints, the failed attempt, the feedback text
of one arm) and returns reply text. None of them sees the planted point or the
target. They read amounts only from the feedback text, so an arm that has no
amounts gives them none.

  unchanged   returns the failed attempt as it is. Must score zero.
  recompute   ignores the feedback and solves from the constraints. Scores the
              same in every arm: the control that shows arms can tie.
  oracle      uses the signed amounts to propose one-step repairs (one or two
              variables) and keeps the first one that satisfies the public
              constraints. With no amounts it returns the attempt unchanged.
  blind       trusts the amounts without checking: it moves one variable by
              the largest amount it is shown.
  verbose     recomputes, but writes a long lead-in first. The lead-in is cut
              by the token cap in every arm, so the reply breaks the format.
"""
import itertools
import re
from fractions import Fraction

_VIOL = re.compile(r"^- (\S+): x(\d+) - x(\d+) <= (-?\d+(?:/\d+)?)(?: \(s ([+-]?\d+(?:/\d+)?)\))?$")


def _lines(vals):
    return "\n".join("x%d = %s" % (i, v) for i, v in enumerate(vals))


def read_feedback(feedback):
    """List of (cid, u, w, bound, amount or None) from the feedback text."""
    out = []
    for ln in feedback.split("\n"):
        m = _VIOL.match(ln)
        if m:
            amt = Fraction(m.group(5)) if m.group(5) is not None else None
            out.append((m.group(1), int(m.group(2)), int(m.group(3)), Fraction(m.group(4)), amt))
    return out


def _satisfies(instance, cand):
    return all(cand[c.u] - cand[c.w] <= c.c for c in instance.constraints)


def unchanged(view):
    return view.attempt_text


def solve(instance):
    d = [Fraction(0)] * instance.n
    for _ in range(instance.n + 2):
        for c in instance.constraints:
            if d[c.w] + c.c < d[c.u]:
                d[c.u] = d[c.w] + c.c
    return d


def recompute(view):
    return _lines(solve(view.instance))


def oracle(view):
    viol = [v for v in read_feedback(view.feedback) if v[4] is not None]
    cands = []
    for _cid, u, w, _b, s in viol:
        for var, delta in ((u, -s), (w, s)):
            if (var, delta) not in cands:
                cands.append((var, delta))
    tries = [[c] for c in cands]
    tries += [[a, b] for a, b in itertools.combinations(cands, 2) if a[0] != b[0]]
    for moves in tries:
        cand = list(view.attempt)
        for var, delta in moves:
            cand[var] = cand[var] + delta
        if _satisfies(view.instance, cand):
            return _lines(cand)
    return view.attempt_text


def blind(view):
    viol = [v for v in read_feedback(view.feedback) if v[4] is not None]
    if not viol:
        return view.attempt_text
    _cid, u, _w, _b, s = max(viol, key=lambda v: abs(v[4]))
    cand = list(view.attempt)
    cand[u] = cand[u] - s
    return _lines(cand)


def verbose(view):
    return "Let me think about this problem step by step before I answer. " * 12 + "\n" + recompute(view)


POLICIES = {"unchanged": unchanged, "recompute": recompute, "oracle": oracle, "blind": blind, "verbose": verbose}
