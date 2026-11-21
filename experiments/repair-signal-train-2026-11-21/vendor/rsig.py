"""Core of the repair-signal experiment, standard library only.

Task: rational difference constraints  v(u) - v(w) <= c  on a small directed
graph, with a required gap v(source) - v(goal) >= L written in the same form.
Checker: needs only the instance and the candidate, returns exact violations.
Arms: four feedback texts that differ only after a failed round.
"""
import hashlib
import json
import re
from fractions import Fraction

ARM_NAMES = ("A", "B", "C", "D")

TIERS = {
    "S": dict(n=4, extra=2, den=2, span=4),
    "M": dict(n=6, extra=5, den=6, span=6),
}


class Constraint:
    __slots__ = ("cid", "u", "w", "c")

    def __init__(self, cid, u, w, c):
        self.cid, self.u, self.w, self.c = cid, u, w, Fraction(c)

    def __eq__(self, o):
        return (self.cid, self.u, self.w, self.c) == (o.cid, o.u, o.w, o.c)

    def __repr__(self):
        return "Constraint(%r,%r,%r,%s)" % (self.cid, self.u, self.w, self.c)

    def text(self):
        return "%s: x%d - x%d <= %s" % (self.cid, self.u, self.w, self.c)


class Instance:
    """constraints includes the goal constraint last, with cid 'goal'.
    planted is only for tests and generation. The checker never reads it."""

    def __init__(self, n, constraints, planted=None, seed=None, tier=None):
        self.n = n
        self.constraints = tuple(constraints)
        self.planted = None if planted is None else tuple(planted)
        self.seed = seed
        self.tier = tier

    def to_dict(self):
        return {"n": self.n, "seed": self.seed, "tier": self.tier,
                "constraints": [[c.cid, c.u, c.w, str(c.c)] for c in self.constraints]}

    def sha256(self):
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()


class Violation:
    __slots__ = ("cid", "u", "w", "c", "excess")

    def __init__(self, cid, u, w, c, excess):
        self.cid, self.u, self.w, self.c, self.excess = cid, u, w, c, excess

    def __eq__(self, o):
        return (self.cid, self.u, self.w, self.c, self.excess) == (o.cid, o.u, o.w, o.c, o.excess)

    def __repr__(self):
        return "Violation(%s,x%d-x%d<=%s,excess=%s)" % (self.cid, self.u, self.w, self.c, self.excess)


# ---------------------------------------------------------------- generator

def _perm(rng, n):
    a = list(range(n))
    for i in range(n - 1, 0, -1):
        j = rng.randrange(i + 1)
        a[i], a[j] = a[j], a[i]
    return a


def make_instance(seed, n=5, extra=4, den=4, span=6, tier=None):
    import random
    rng = random.Random(seed)
    p = [Fraction(rng.randint(-span * den, span * den), den) for _ in range(n)]
    if max(p) == min(p):
        p[0] += 1
    hi = max(range(n), key=lambda i: (p[i], -i))
    lo = min(range(n), key=lambda i: (p[i], i))
    order = _perm(rng, n)
    pairs = [(order[i], order[(i + 1) % n]) for i in range(n)]
    seen = set(pairs)
    tries = 0
    while len(pairs) < n + extra and tries < 200:
        tries += 1
        u, w = rng.randrange(n), rng.randrange(n)
        if u != w and (u, w) not in seen:
            seen.add((u, w))
            pairs.append((u, w))
    pairs = [pairs[i] for i in _perm(rng, len(pairs))]
    cons = []
    for i, (u, w) in enumerate(pairs):
        slack = Fraction(0) if rng.randrange(3) == 0 else Fraction(rng.randint(1, 3 * den), den)
        cons.append(Constraint("c%d" % i, u, w, p[u] - p[w] + slack))
    units = int((p[hi] - p[lo]) * den)
    L = Fraction(units - rng.randint(0, units // 2), den)
    cons.append(Constraint("goal", lo, hi, -L))
    return Instance(n, cons, planted=p, seed=seed, tier=tier)


def make_suite(base_seed, count, tier):
    return [make_instance(base_seed + i, tier=tier, **TIERS[tier]) for i in range(count)]


# ------------------------------------------------------------------ checker

def check(instance, candidate):
    """Exact, label-free. Returns [] on pass, else the violations in
    constraint order, each with its signed exact excess (left side minus bound)."""
    if len(candidate) != instance.n:
        raise ValueError("candidate length")
    for x in candidate:
        if isinstance(x, bool) or not isinstance(x, (Fraction, int)):
            raise TypeError("candidate must hold exact Fractions or ints")
    out = []
    for c in instance.constraints:
        excess = (candidate[c.u] - candidate[c.w]) - c.c
        if excess > 0:
            out.append(Violation(c.cid, c.u, c.w, c.c, Fraction(excess)))
    return out


# ------------------------------------------------------------------- parser

_LINE = re.compile(r"x([0-9]+)[ \t]*=[ \t]*(-?[0-9]{1,12})(?:/([0-9]{1,12}))?", re.ASCII)
_FENCE = re.compile(r"```[A-Za-z]*\n(.*?)\n?```", re.S)


def parse_candidate(reply, n):
    """Strict. Returns (list_of_Fraction, None) or (None, error_text).
    The reply must be only lines 'xI = p' or 'xI = p/q', optionally inside
    one code fence, one line for each of x0..x(n-1), no other text."""
    body = reply.strip()
    m = _FENCE.fullmatch(body)
    if m:
        body = m.group(1)
    if not body.strip():
        return None, "the reply was empty"
    vals = {}
    for ln, raw in enumerate(body.split("\n"), 1):
        line = raw.strip()
        if not line:
            continue
        g = _LINE.fullmatch(line)
        if not g:
            return None, "line %d is not of the form 'x0 = 3/2'" % ln
        idx_s, num_s, den_s = g.groups()
        if str(int(idx_s)) != idx_s or int(idx_s) >= n:
            return None, "line %d names an unknown variable" % ln
        idx = int(idx_s)
        if idx in vals:
            return None, "variable x%d appears twice" % idx
        den = int(den_s) if den_s is not None else 1
        if den == 0:
            return None, "line %d has a zero denominator" % ln
        vals[idx] = Fraction(int(num_s), den)
    for i in range(n):
        if i not in vals:
            return None, "variable x%d is missing" % i
    return [vals[i] for i in range(n)], None


def canon(candidate):
    return ";".join(str(x) for x in candidate)


# ------------------------------------------------------------ prompts, arms

REPLY_TAIL = "Reply with a corrected assignment, one line per variable, and nothing else."
EXCESS_NOTE = "The excess is the left side minus the bound."


def initial_prompt(instance):
    lines = [
        "Find rational numbers x0 to x%d that satisfy every constraint below." % (instance.n - 1),
        "Each constraint has the form  xU - xW <= c.",
        "The constraint named goal makes x%d - x%d at least %s, so all zeros does not work."
        % (instance.constraints[-1].w, instance.constraints[-1].u, -instance.constraints[-1].c),
        "",
    ]
    lines += [c.text() for c in instance.constraints]
    lines += ["", "Reply with exactly one line per variable, like  x0 = 3/2  or  x1 = -2,",
              "for x0 to x%d, and nothing else." % (instance.n - 1)]
    return "\n".join(lines)


def signed(f):
    f = Fraction(f)
    return ("+" if f > 0 else "") + str(f)


def _viol_lines(vios, excess_sign):
    out = []
    for v in vios:
        s = "- %s: x%d - x%d <= %s" % (v.cid, v.u, v.w, v.c)
        if excess_sign is not None:
            s += " (excess %s)" % signed(excess_sign * v.excess)
        out.append(s)
    return out


def feedback_unparsed(error):
    """Same for every arm. It says nothing about the constraints."""
    return "Verdict: FAILED. Your reply could not be read: %s.\n%s" % (error, REPLY_TAIL)


def feedback_A(vios):
    return "Verdict: FAILED.\n" + REPLY_TAIL


def feedback_B(vios):
    return "\n".join(["Verdict: FAILED. Violated constraints:"] + _viol_lines(vios, None) + [REPLY_TAIL])


def feedback_C(vios):
    return "\n".join(["Verdict: FAILED. Violated constraints:"] + _viol_lines(vios, 1)
                     + [EXCESS_NOTE, REPLY_TAIL])


def feedback_D(vios):
    return "\n".join(["Verdict: FAILED. Violated constraints:"] + _viol_lines(vios, -1)
                     + [EXCESS_NOTE, REPLY_TAIL])


ARMS = {"A": feedback_A, "B": feedback_B, "C": feedback_C, "D": feedback_D}


def feedback(arm, vios):
    return ARMS[arm](vios)
