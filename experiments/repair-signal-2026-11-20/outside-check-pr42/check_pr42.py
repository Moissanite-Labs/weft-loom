"""Recount of an outside post-hoc study of this record's logs. Not part of the registered analysis.

It reads the four logs in ../results/ and prints every number that CHECK.md and the README additions state. It shares no
code with the harness or with the recount. Every test is the exact binomial sign test in integers and fractions.
The one sampled step is the label-swap correction in section 5, which uses a fixed seed.

Definitions, applied the same way to every model, tier and arm. A unit is one (arm, instance).
- readable round: parse_error is null. Unreadable round: parse_error is not null.
- pass4: some round has verdict pass.
- esc: some round is unreadable. pure: pass4 and not esc.
- r1fail: round 1 is readable and failed. r2esc: r1fail and round 2 is unreadable. r2pass: r1fail and round 2 passed.
- solve time: the sum of seconds over rounds 1 to the passing round.
- late pass: pass4 and solve time above 30 seconds.
- An instance is dropped from an X-against-Y test when the round 1 reply differs between X and Y.
- Sign test: exact one-sided binomial on the discordant pairs, tail(w, n) = sum over k >= w of C(n, k) / 2^n.
  Two-sided p is min(1, 2 * tail(max(w, l), n)).
- Lenient reading (a heuristic, not a registered rule): the last number written as `xI = number` for each variable
  anywhere in a reply, checked against every constraint with fractions. It is used only to say that an unreadable reply
  held a satisfying assignment.

Usage: python3 -I -B check_pr42.py
"""
import json
import os
import random
import re
import sys
from fractions import Fraction
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
QWEN = "Qwen3.8-27B-AD-Q4_K_M"
GEMMA = "gemma-4-E4B-it-Q8_0"
ARMS = "ABCD"
WINDOWS = (5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 300)
CONSTRAINT = re.compile(r"^(\w+): x(\d+) - x(\d+) <= (-?\d+(?:/\d+)?)$")
VARIABLES = re.compile(r"x0 to x(\d+)")
WRITTEN = re.compile(r"(?<![A-Za-z0-9_])x(\d+)\s*=\s*(-?\d+(?:\.\d+)?(?:/\d+)?)")
ANSWER_LINE = re.compile(r"^\s*x\d+\s*=\s*[-+]?\d+(\.\d+)?(/\d+)?\s*$")
SEEDS = (271828, 99)
DRAWS = 100000


class CheckError(Exception):
    pass


# ---------------------------------------------------------------- loading

def load_log(path):
    """Return {arm: {instance: [round records sorted by round]}}. Refuses a log that is not four complete arms."""
    units = {}
    seen = set()
    try:
        with open(path, encoding="utf-8") as fh:
            lines = [line for line in fh if line.strip()]
    except OSError as exc:
        raise CheckError("cannot read %s: %s" % (path, exc))
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except ValueError:
            raise CheckError("line %d is not JSON" % number)
        if row.get("type") != "round":
            continue
        key = (row["arm"], row["instance"], row["round"])
        if key in seen:
            raise CheckError("duplicate round %r" % (key,))
        seen.add(key)
        units.setdefault(row["arm"], {}).setdefault(row["instance"], []).append(row)
    if sorted(units) != list(ARMS):
        raise CheckError("arms found %r, need %r" % (sorted(units), list(ARMS)))
    ids = [set(units[a]) for a in ARMS]
    if any(s != ids[0] for s in ids):
        raise CheckError("arms do not cover the same instances")
    for arm in ARMS:
        for inst, rounds in units[arm].items():
            rounds.sort(key=lambda r: r["round"])
            if [r["round"] for r in rounds] != list(range(1, len(rounds) + 1)):
                raise CheckError("rounds of %s %s are not 1..n" % (arm, inst))
    return units


def instance_of(rounds):
    """(n variables, constraints) read from the logged first prompt."""
    prompt = rounds[0]["prompt"]
    m = VARIABLES.search(prompt)
    cons = []
    for line in prompt.splitlines():
        c = CONSTRAINT.match(line.strip())
        if c:
            cons.append((int(c.group(2)), int(c.group(3)), Fraction(c.group(4))))
    if not m or not cons:
        raise CheckError("first prompt has no instance")
    return int(m.group(1)) + 1, cons


def readable(r):
    return r["parse_error"] is None


def passed(r):
    return r["verdict"] == "pass"


def excess_sum(r):
    return sum((Fraction(v["excess"]) for v in r["violations"]), Fraction(0))


def seconds(r):
    return Fraction(repr(r["seconds"]))


# ---------------------------------------------------------------- statistics

def tail(w, n):
    return Fraction(sum(comb(n, k) for k in range(w, n + 1)), 2 ** n)


def two_sided(a, b):
    n = a + b
    return min(Fraction(1), 2 * tail(max(a, b), n)) if n else Fraction(1)


def fmt(p):
    p = Fraction(p)
    if p.denominator <= 4096 * 64:
        return "%s = %s" % (p, "%.4g" % float(p))
    return "%.4g" % float(p)


def pair(x, y, ids):
    """(x only, y only) over the instances in ids, x and y are {instance: bool}."""
    a = sum(1 for i in ids if x[i] and not y[i])
    b = sum(1 for i in ids if y[i] and not x[i])
    return a, b


def paired_ids(units, x_arm, y_arm):
    ids = sorted(units[x_arm])
    keep = [i for i in ids if units[x_arm][i][0]["reply_sha256"] == units[y_arm][i][0]["reply_sha256"]]
    return keep, len(ids) - len(keep)


def holm(ps, alpha=Fraction(5, 100)):
    """Holm step-down. ps is {name: Fraction}. Returns {name: adjusted p}."""
    order = sorted(ps, key=lambda k: (ps[k], k))
    m = len(order)
    out, running = {}, Fraction(0)
    for rank, name in enumerate(order):
        running = max(running, min(Fraction(1), (m - rank) * ps[name]))
        out[name] = running
    return out


def quantile(values, num, den):
    v = sorted(values)
    return v[(len(v) * num) // den] if v else None


# ---------------------------------------------------------------- unit features

class Tier:
    def __init__(self, units):
        self.units = units
        self.ids = sorted(units["A"])
        self.shape = {i: instance_of(units["A"][i]) for i in self.ids}
        self.feat = {a: {i: self.features(units[a][i]) for i in self.ids} for a in ARMS}

    def features(self, rounds):
        pass_round = next((r["round"] for r in rounds if passed(r)), None)
        esc = any(not readable(r) for r in rounds)
        r1 = rounds[0]
        r1fail = readable(r1) and r1["verdict"] == "fail"
        r2 = rounds[1] if len(rounds) > 1 else None
        solve_time = None
        if pass_round is not None:
            solve_time = sum((seconds(r) for r in rounds[:pass_round]), Fraction(0))
        return {
            "pass4": pass_round is not None,
            "pass_round": pass_round,
            "esc": esc,
            "pure": pass_round is not None and not esc,
            "r1fail": r1fail,
            "r2esc": bool(r1fail and r2 is not None and not readable(r2)),
            "r2pass": bool(r1fail and r2 is not None and passed(r2)),
            "r2readable": bool(r1fail and r2 is not None and readable(r2)),
            "solve_time": solve_time,
            "total_time": sum((seconds(r) for r in rounds), Fraction(0)),
        }

    def flag(self, arm, name):
        return {i: bool(self.feat[arm][i][name]) for i in self.ids}

    def within(self, arm, limit):
        return {i: self.feat[arm][i]["solve_time"] is not None and self.feat[arm][i]["solve_time"] <= limit for i in self.ids}

    def late(self, arm, limit=30):
        return {i: self.feat[arm][i]["solve_time"] is not None and self.feat[arm][i]["solve_time"] > limit for i in self.ids}

    def lenient(self, inst, reply):
        n = self.shape[inst][0]
        last = {}
        for m in WRITTEN.finditer(reply):
            text = m.group(2)
            top, _, bottom = text.partition("/")
            if bottom and int(bottom) == 0:
                continue
            last[int(m.group(1))] = Fraction(top) / (int(bottom) if bottom else 1)
        if sorted(last) != list(range(n)):
            return None
        return last

    def lenient_ok(self, inst, reply):
        v = self.lenient(inst, reply)
        return v is not None and all(v[u] - v[w] - c <= 0 for u, w, c in self.shape[inst][1])

    def any_format_r2(self, arm):
        """Round 2 solved in any format, among instances whose round 1 failed readably."""
        out = {}
        for i in self.ids:
            f = self.feat[arm][i]
            r2 = self.units[arm][i][1] if len(self.units[arm][i]) > 1 else None
            out[i] = bool(f["r1fail"] and r2 is not None and (passed(r2) or (not readable(r2) and self.lenient_ok(i, r2["reply"]))))
        return out


# ---------------------------------------------------------------- reporting helpers

def line(text=""):
    print(text)


def sign_line(label, a, b, first, second, two=False):
    p = tail(max(a, b), a + b) if (a + b) else Fraction(1)
    one = tail(a, a + b) if (a + b) else Fraction(1)
    text = "%s: %s %d, %s %d, one-sided p for the first %s" % (label, first, a, second, b, fmt(one))
    if two:
        text += ", two-sided p %s" % fmt(two_sided(a, b))
    line(text)
    return p


def per_arm(label, values):
    line("%s: %s" % (label, ", ".join("%s %s" % (a, values[a]) for a in ARMS)))


# ---------------------------------------------------------------- sections

def section_totals(name, t):
    line("[%s] four-round passes, escapes and time" % name)
    per_arm("passed within 4 rounds", {a: sum(1 for i in t.ids if t.feat[a][i]["pass4"]) for a in ARMS})
    per_arm("passed with no unreadable round", {a: sum(1 for i in t.ids if t.feat[a][i]["pure"]) for a in ARMS})
    per_arm("units with an unreadable round", {a: sum(1 for i in t.ids if t.feat[a][i]["esc"]) for a in ARMS})
    per_arm("round 1 failed readably (instances)", {a: sum(1 for i in t.ids if t.feat[a][i]["r1fail"]) for a in ARMS})
    per_arm("round 2 unreadable among those", {a: sum(1 for i in t.ids if t.feat[a][i]["r2esc"]) for a in ARMS})
    per_arm("round 2 passes among those", {a: sum(1 for i in t.ids if t.feat[a][i]["r2pass"]) for a in ARMS})
    total = {a: sum((t.feat[a][i]["total_time"] for i in t.ids), Fraction(0)) for a in ARMS}
    per_arm("total seconds", {a: "%.0f" % float(total[a]) for a in ARMS})
    line("total seconds, D over C: %.3f" % float(total["D"] / total["C"]))
    line("round 1 replies equal in every arm: %d of %d instances" % (
        sum(1 for i in t.ids if len({t.units[a][i][0]["reply_sha256"] for a in ARMS}) == 1), len(t.ids)))


def section_pairs(name, t):
    line("[%s] paired comparisons, sign tests in exact arithmetic" % name)

    def cmp(label, x_arm, y_arm, x, y, first, second, ids=None):
        keep, dropped = paired_ids(t.units, x_arm, y_arm)
        use = keep if ids is None else [i for i in keep if i in ids]
        a, b = pair(x, y, use)
        sign_line("%s (%d instances, %d dropped for a different round 1)" % (label, len(use), dropped), a, b, first, second, two=True)
        return a, b

    cmp("four-round pass, C against B", "C", "B", t.flag("C", "pass4"), t.flag("B", "pass4"), "C only", "B only")
    cmp("four-round pass, D against C", "D", "C", t.flag("D", "pass4"), t.flag("C", "pass4"), "D only", "C only")
    cmp("four-round pass, C against D", "C", "D", t.flag("C", "pass4"), t.flag("D", "pass4"), "C only", "D only")
    cmp("round 2 unreadable, D against C", "D", "C", t.flag("D", "r2esc"), t.flag("C", "r2esc"), "D only", "C only")
    cmp("round 2 unreadable, B against C", "B", "C", t.flag("B", "r2esc"), t.flag("C", "r2esc"), "B only", "C only")
    cmp("round 2 unreadable, D against B", "D", "B", t.flag("D", "r2esc"), t.flag("B", "r2esc"), "D only", "B only")
    cmp("round 2 unreadable, A against C", "A", "C", t.flag("A", "r2esc"), t.flag("C", "r2esc"), "A only", "C only")
    cmp("pass with no unreadable round, C against D", "C", "D", t.flag("C", "pure"), t.flag("D", "pure"), "C only", "D only")
    cmp("round 2 pass, C against D", "C", "D", t.flag("C", "r2pass"), t.flag("D", "r2pass"), "C only", "D only")
    both_readable = {i for i in t.ids if t.feat["C"][i]["r2readable"] and t.feat["D"][i]["r2readable"]}
    cmp("round 2 pass with both arms readable at round 2 (%d instances), C against D" % len(both_readable), "C", "D",
        t.flag("C", "r2pass"), t.flag("D", "r2pass"), "C only", "D only", both_readable)
    cmp("late pass (over 30 s), D against C", "D", "C", t.late("D"), t.late("C"), "D only", "C only")
    neither = {i for i in t.ids if not t.feat["C"][i]["esc"] and not t.feat["D"][i]["esc"]}
    cmp("four-round pass where neither arm had an unreadable round (%d instances), C against D" % len(neither),
                    "C", "D", t.flag("C", "pass4"), t.flag("D", "pass4"), "C only", "D only", neither)
    line("  passes in that set: C %d, D %d" % (
        sum(1 for i in neither if t.feat["C"][i]["pass4"]), sum(1 for i in neither if t.feat["D"][i]["pass4"])))
    pure_c_only = [i for i in t.ids if t.feat["C"][i]["pure"] and not t.feat["D"][i]["pure"]]
    line("  of the %d instances C passed with no unreadable round and D did not: D had an unreadable round in %d, and passed in %d of those" % (
        len(pure_c_only), sum(1 for i in pure_c_only if t.feat["D"][i]["esc"]),
        sum(1 for i in pure_c_only if t.feat["D"][i]["esc"] and t.feat["D"][i]["pass4"])))


def section_windows(name, t):
    line("[%s] passes within a seconds budget (cumulative logged seconds), per arm, then C against D" % name)
    for limit in WINDOWS:
        flags = {a: t.within(a, limit) for a in ARMS}
        counts = {a: sum(flags[a].values()) for a in ARMS}
        c_only, d_only = pair(flags["C"], flags["D"], t.ids)
        line("  at most %3d s: A %d, B %d, C %d, D %d | C only %d, D only %d, one-sided p for C %s" % (
            limit, counts["A"], counts["B"], counts["C"], counts["D"], c_only, d_only, fmt(tail(c_only, c_only + d_only))))
    unbounded = {a: t.flag(a, "pass4") for a in ARMS}
    line("  unbounded: C %d, D %d" % (sum(unbounded["C"].values()), sum(unbounded["D"].values())))


def section_split(name, t):
    line("[%s] C against D, split by whether the arm itself had an unreadable round" % name)
    split = {}
    for a in ("C", "D"):
        for esc in (False, True):
            ids = [i for i in t.ids if t.feat[a][i]["esc"] == esc]
            split[(a, esc)] = (sum(1 for i in ids if t.feat[a][i]["pass4"]), len(ids))
            line("  %s, %s: %d of %d passed" % (a, "some unreadable round" if esc else "no unreadable round", *split[(a, esc)]))
    d_pure = sum(1 for i in t.ids if t.feat["C"][i]["pure"]) - sum(1 for i in t.ids if t.feat["D"][i]["pure"])
    d_late = sum(1 for i in t.ids if t.feat["C"][i]["pass4"] and t.feat["C"][i]["esc"]) - \
        sum(1 for i in t.ids if t.feat["D"][i]["pass4"] and t.feat["D"][i]["esc"])
    d_all = sum(1 for i in t.ids if t.feat["C"][i]["pass4"]) - sum(1 for i in t.ids if t.feat["D"][i]["pass4"])
    line("  C minus D passes: no unreadable round %+d, after an unreadable round %+d, overall %+d (sum check %s)" % (
        d_pure, d_late, d_all, "holds" if d_pure + d_late == d_all else "FAILS"))
    signs = []
    for esc in (False, True):
        (c_pass, c_n), (d_pass, d_n) = split[("C", esc)], split[("D", esc)]
        if c_n == 0 or d_n == 0:
            signs.append(0)  # an empty stratum cannot show a direction
            continue
        c_rate, d_rate = Fraction(c_pass, c_n), Fraction(d_pass, d_n)
        signs.append((c_rate > d_rate) - (c_rate < d_rate))
    total = (d_all > 0) - (d_all < 0)
    line("  direction of C minus D in the two strata (1 C higher, -1 D higher): %s, overall: %d" % (signs, total))
    line("  a reversal (the same non-zero direction in both strata and the opposite one overall): %s" % (
        "yes" if signs[0] == signs[1] != 0 and total == -signs[0] else "no"))
    line("  the split variable depends on the arm: units of C and D with different split status on the same instance: %d" % sum(
        1 for i in t.ids if t.feat["C"][i]["esc"] != t.feat["D"][i]["esc"]))
    # a split fixed before any reply: round 1 summed excess, the same in C and D when round 1 is the same
    groups = {}
    for i in t.ids:
        r1 = t.units["C"][i][0]
        if not readable(r1):
            key = "round 1 unreadable"
        elif passed(r1):
            key = "round 1 passed"
        else:
            e = excess_sum(r1)
            key = "excess at most 1" if e <= 1 else ("excess over 1, at most 3" if e <= 3 else "excess over 3")
        groups.setdefault(key, []).append(i)
    same_round1 = all(t.units["C"][i][0]["reply_sha256"] == t.units["D"][i][0]["reply_sha256"] for i in t.ids)
    line("  split by round 1 (set before any arm differs; round 1 identical in C and D on every instance: %s)" % same_round1)
    worst = True
    for key in sorted(groups):
        c = sum(1 for i in groups[key] if t.feat["C"][i]["pass4"])
        d = sum(1 for i in groups[key] if t.feat["D"][i]["pass4"])
        worst = worst and d >= c
        line("    %s: %d instances, C passes %d, D passes %d" % (key, len(groups[key]), c, d))
    line("  D at least C in every round 1 group: %s" % worst)
    joint = {}
    for i in t.ids:
        joint.setdefault((t.feat["C"][i]["esc"], t.feat["D"][i]["esc"]), []).append(i)
    for key in sorted(joint):
        ids = joint[key]
        line("  C %s, D %s: %d instances, C passes %d, D passes %d" % (
            "escapes" if key[0] else "never escapes", "escapes" if key[1] else "never escapes", len(ids),
            sum(1 for i in ids if t.feat["C"][i]["pass4"]), sum(1 for i in ids if t.feat["D"][i]["pass4"])))


def section_excess(name, t):
    """Round 2 summed excess, C against D, among instances readable and failed in round 1 and readable in round 2 in both."""
    ids = [i for i in t.ids if t.feat["C"][i]["r2readable"] and t.feat["D"][i]["r2readable"]]
    below = sum(1 for i in ids if excess_sum(t.units["C"][i][1]) < excess_sum(t.units["D"][i][1]))
    above = sum(1 for i in ids if excess_sum(t.units["C"][i][1]) > excess_sum(t.units["D"][i][1]))
    line("[%s] round 2 summed excess among the %d instances readable at round 2 in both C and D: C below D on %d, D below C on %d, "
         "one-sided p for C %s" % (name, len(ids), below, above, fmt(tail(below, below + above))))


def section_lenient(name, t):
    line("[%s] unreadable replies that already held a satisfying assignment (lenient reading, a heuristic)" % name)
    per_arm("unreadable replies", {a: sum(1 for i in t.ids for r in t.units[a][i] if not readable(r)) for a in ARMS})
    per_arm("of them satisfying under the lenient reading", {
        a: sum(1 for i in t.ids for r in t.units[a][i] if not readable(r) and t.lenient_ok(i, r["reply"])) for a in ARMS})
    per_arm("round 2 solved in any format, of the round 2 reads", {a: sum(t.any_format_r2(a).values()) for a in ARMS})
    cd = pair(t.any_format_r2("C"), t.any_format_r2("D"), t.ids)
    sign_line("round 2 solved in any format, C against D", cd[0], cd[1], "C only", "D only", two=True)
    only = [i for i in t.ids if t.feat["C"][i]["r2pass"] and not t.feat["D"][i]["r2pass"]]
    d_unreadable = [i for i in only if t.feat["D"][i]["r2esc"]]
    line("  instances where C passed round 2 and D did not: %d. D unreadable in %d of them. Unreadable D reply held a satisfying "
         "assignment in %d. D passed at round 3 in %d" % (
             len(only), len(d_unreadable), sum(1 for i in d_unreadable if t.lenient_ok(i, t.units["D"][i][1]["reply"])),
             sum(1 for i in d_unreadable if len(t.units["D"][i]) > 2 and passed(t.units["D"][i][2]))))
    line("  unreadable round 2 seconds (D, those instances): min %s, max %s; C round 2 seconds on the same instances: min %s, max %s" % (
        "%.1f" % float(min(seconds(t.units["D"][i][1]) for i in d_unreadable)) if d_unreadable else "none",
        "%.1f" % float(max(seconds(t.units["D"][i][1]) for i in d_unreadable)) if d_unreadable else "none",
        "%.1f" % float(min(seconds(t.units["C"][i][1]) for i in d_unreadable)) if d_unreadable else "none",
        "%.1f" % float(max(seconds(t.units["C"][i][1]) for i in d_unreadable)) if d_unreadable else "none"))


def section_correction(t):
    """One-sided label-swap correction over the C-over-D statistics, the direction the plan registered."""
    names = ["pass within %d s" % w for w in WINDOWS] + ["pass with no unreadable round", "round 2 pass"]
    index = {i: k for k, i in enumerate(t.ids)}

    def mask(flags):
        m = 0
        for i, v in flags.items():
            if v:
                m |= 1 << index[i]
        return m

    cm = [mask(t.within("C", w)) for w in WINDOWS] + [mask(t.flag("C", "pure")), mask(t.flag("C", "r2pass"))]
    dm = [mask(t.within("D", w)) for w in WINDOWS] + [mask(t.flag("D", "pure")), mask(t.flag("D", "r2pass"))]
    cache = {}

    def p_of(w, l):
        key = (w, l)
        if key not in cache:
            cache[key] = float(tail(w, w + l)) if w + l else 1.0
        return cache[key]

    observed = [p_of((c & ~d).bit_count(), (d & ~c).bit_count()) for c, d in zip(cm, dm)]
    full = (1 << len(t.ids)) - 1
    line("[Qwen S] one-sided label-swap (min-p) correction over %d C-over-D statistics, %d draws per seed, sampled" % (len(names), DRAWS))
    for seed in SEEDS:
        rng = random.Random(seed)
        hits = [0] * len(names)
        for _ in range(DRAWS):
            m = rng.getrandbits(len(t.ids)) & full
            low = 1.0
            for c, d in zip(cm, dm):
                c2 = (c & ~m) | (d & m)
                d2 = (d & ~m) | (c & m)
                p = p_of((c2 & ~d2).bit_count(), (d2 & ~c2).bit_count())
                if p < low:
                    low = p
            for k, o in enumerate(observed):
                if low <= o:
                    hits[k] += 1
        for k in (4, 6, 11, 12):
            line("  seed %d, %s: raw one-sided p %.4f, adjusted %.4f" % (seed, names[k], observed[k], hits[k] / DRAWS))


def section_gemma(g):
    line("[gemma] held-out tests of the claims, one-sided in the claimed direction, Holm step-down over 8 tests at 0.05")
    ps, counts = {}, {}
    plan = (
        ("G1 round 2 unreadable, D over C", "D", "C", "r2esc"),
        ("G2 pass with no unreadable round, C over D", "C", "D", "pure"),
        ("G3 round 2 pass, C over D", "C", "D", "r2pass"),
        ("G4 four-round pass, D over C", "D", "C", "pass4"),
    )
    for tier in ("S", "M"):
        t = g[tier]
        for label, x, y, name in plan:
            keep, dropped = paired_ids(t.units, x, y)
            a, b = pair(t.flag(x, name), t.flag(y, name), keep)
            key = "%s %s" % (label.split(" ")[0], tier)
            ps[key] = tail(a, a + b) if a + b else Fraction(1)
            counts[key] = (label, a, b, dropped)
    adj = holm(ps)
    for key in sorted(ps):
        label, a, b, dropped = counts[key]
        reverse = tail(b, a + b) if a + b else Fraction(1)
        line("  %s: %s %d against %d (dropped %d), one-sided p %s, Holm %.4f, p in the other direction %.4f" % (
            key, label[3:].split(",")[0], a, b, dropped, fmt(ps[key]), float(adj[key]), float(reverse)))
    for tier in ("S", "M"):
        t = g[tier]
        neither = {i for i in t.ids if not t.feat["C"][i]["esc"] and not t.feat["D"][i]["esc"]}
        a, b = pair(t.flag("C", "pass4"), t.flag("D", "pass4"), sorted(neither))
        line("  G8 %s, four-round pass where neither arm was unreadable (%d instances), C only %d, D only %d, one-sided p %s" % (
            tier, len(neither), a, b, fmt(tail(a, a + b))))
        total = {x: sum((t.feat[x][i]["total_time"] for i in t.ids), Fraction(0)) for x in "CD"}
        line("  G6 %s, total seconds D over C %.3f" % (tier, float(total["D"] / total["C"])))
        a, b = pair(t.within("C", 30), t.within("D", 30), t.ids)
        line("  %s passes within 30 s: C %d, D %d (C only %d, D only %d)" % (
            tier, sum(t.within("C", 30).values()), sum(t.within("D", 30).values()), a, b))
        for arm in ARMS:
            times = [seconds(r) for i in t.ids for r in t.units[arm][i] if readable(r)]
            line("  %s arm %s readable rounds: %d, 10th %.1f, median %.1f, 90th %.1f seconds" % (
                tier, arm, len(times), float(quantile(times, 1, 10)), float(quantile(times, 1, 2)), float(quantile(times, 9, 10))))
        kinds = {a: {"decimal": 0, "other answer": 0, "prose": 0} for a in ARMS}
        for arm in ARMS:
            for i in t.ids:
                if t.feat[arm][i]["r2esc"]:
                    kinds[arm][reply_kind(t.units[arm][i][1]["reply"])] += 1
        line("  G9 %s, kind of round 2 unreadable reply: %s" % (tier, "; ".join(
            "%s decimal %d, other answer %d, prose %d" % (a, kinds[a]["decimal"], kinds[a]["other answer"], kinds[a]["prose"]) for a in ARMS)))
        section_excess("gemma %s" % tier, t)


def reply_kind(reply):
    text = reply.strip()
    if text.startswith("```") and text.endswith("```") and text.count("```") == 2:
        text = text[3:-3].split("\n", 1)[1] if "\n" in text[3:-3] else ""
    lines = [x for x in text.split("\n") if x.strip()]
    if lines and all(ANSWER_LINE.match(x) for x in lines):
        return "decimal" if any("." in x for x in lines) else "other answer"
    return "prose"


def main():
    data = {}
    for model, key in ((QWEN, "qwen"), (GEMMA, "gemma")):
        data[key] = {}
        for tier in ("S", "M"):
            data[key][tier] = Tier(load_log(os.path.join(RESULTS, "%s-%s.jsonl" % (model, tier))))
    line("section 1: totals")
    for key, label in (("qwen", "Qwen"), ("gemma", "gemma")):
        for tier in ("S", "M"):
            section_totals("%s %s" % (label, tier), data[key][tier])
    line()
    line("section 2: paired comparisons")
    for key, label in (("qwen", "Qwen"), ("gemma", "gemma")):
        for tier in ("S", "M"):
            section_pairs("%s %s" % (label, tier), data[key][tier])
    line()
    line("section 3: budgets and the split by unreadable rounds")
    for tier in ("S", "M"):
        section_windows("Qwen %s" % tier, data["qwen"][tier])
        section_split("Qwen %s" % tier, data["qwen"][tier])
        section_excess("Qwen %s" % tier, data["qwen"][tier])
    section_windows("gemma S", data["gemma"]["S"])
    line()
    line("section 4: unreadable replies that held an answer")
    for key, label in (("qwen", "Qwen"), ("gemma", "gemma")):
        for tier in ("S", "M"):
            section_lenient("%s %s" % (label, tier), data[key][tier])
    line()
    line("section 5: multiplicity")
    section_correction(data["qwen"]["S"])
    line()
    line("section 6: held-out tests on gemma")
    section_gemma(data["gemma"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CheckError as exc:
        sys.exit("CHECK_FAIL: " + str(exc))
