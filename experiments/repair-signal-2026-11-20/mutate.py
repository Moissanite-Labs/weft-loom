"""Mutation check. Copies the harness to a temp dir, applies one deliberate
break at a time, runs the unit tests and the self-test there, and requires
that something goes red. A mutation that leaves everything green means a
check is missing, and this script exits 1."""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["rsig.py", "runner.py", "analyze.py", "stats.py", "selftest.py", "recount.py"]

# (name, file, old text, new text)
MUTATIONS = [
    ("checker uses < instead of >", "rsig.py", "if excess > 0:", "if excess < 0:"),
    ("checker treats the boundary as a violation", "rsig.py", "if excess > 0:", "if excess >= 0:"),
    ("checker drops the goal constraint", "rsig.py", "for c in instance.constraints:\n        excess",
     "for c in instance.constraints[:-1]:\n        excess"),
    ("checker rounds through float", "rsig.py", "excess = (candidate[c.u] - candidate[c.w]) - c.c",
     "excess = Fraction(float((candidate[c.u] - candidate[c.w]) - c.c))"),
    ("checker reads the planted point", "rsig.py", "        excess = (candidate[c.u]",
     "        if instance.planted is not None: return []\n        excess = (candidate[c.u]"),
    ("generator makes the goal too weak", "rsig.py", "L = Fraction(units - rng.randint(0, units // 2), den)",
     "L = Fraction(0)"),
    ("generator plants an infeasible point", "rsig.py", "cons.append(Constraint(\"c%d\" % i, u, w, p[u] - p[w] + slack))",
     "cons.append(Constraint(\"c%d\" % i, u, w, p[u] - p[w] - slack - Fraction(1, den)))"),
    ("generator ignores the seed", "rsig.py", "rng = random.Random(seed)", "rng = random.Random(0)"),
    ("parser accepts trailing prose", "rsig.py", "g = _LINE.fullmatch(line)", "g = _LINE.match(line)"),
    ("parser accepts a repeated variable", "rsig.py", 'if idx in vals:\n            return None, "variable x%d appears twice" % idx',
     "if False:\n            return None, 'x'"),
    ("arm D does not flip the sign", "rsig.py", "+ _viol_lines(vios, -1)", "+ _viol_lines(vios, 1)"),
    ("arm C hides the amount", "rsig.py", "return \"\\n\".join([\"Verdict: FAILED. Violated constraints:\"] + _viol_lines(vios, 1)\n                     + [EXCESS_NOTE, REPLY_TAIL])",
     "return \"\\n\".join([\"Verdict: FAILED. Violated constraints:\"] + _viol_lines(vios, None)\n                     + [EXCESS_NOTE, REPLY_TAIL])"),
    ("arm A names the constraints", "rsig.py", 'return "Verdict: FAILED.\\n" + REPLY_TAIL',
     'return feedback_B(vios)'),
    ("arm leaks into the first prompt", "runner.py", 'messages = [{"role": "user", "content": rsig.initial_prompt(instance)}]',
     'messages = [{"role": "user", "content": rsig.initial_prompt(instance) + "\\n(arm %s)" % arm}]'),
    ("verdict taken from the reply", "runner.py", "vios = rsig.check(instance, cand)",
     "vios = rsig.check(instance, cand)[:0]"),
    ("round limit off by one", "runner.py", "for r in range(1, k + 1):", "for r in range(1, k + 2):"),
    ("resume key ignores the tier", "runner.py", 'rec["tier"], rec["instance"], rec["k"])] = rec["instance_sha256"]',
     '"", rec["instance"], rec["k"])] = rec["instance_sha256"]'),
    ("resume key ignores the tier (write side)", "runner.py", "key = (model, arm, inst.tier, inst.seed, k)",
     "key = (model, arm, '', inst.seed, k)"),
    ("torn log line is not fenced off", "runner.py", 'if f.read(1) != "\\n":', "if False:"),
    ("temperature not zero", "runner.py", '"temperature": 0,', '"temperature": 0.7,'),
    ("mock follow ignores the sign", "runner.py", "step = Fraction(ex) if ex is not None else Fraction(1)",
     "step = abs(Fraction(ex)) if ex is not None else Fraction(1)"),
    ("ignore mock reads the feedback", "runner.py", "if rnd < at:", "if rnd < at or len(messages[-1]['content']) % 2:"),
    ("sign test tail wrong", "stats.py", "return float(upper(wins))", "return float(upper(wins + 1))"),
    ("sign flip counts the wrong tail", "stats.py", "if s >= obs", "if s <= obs"),
    ("pairing breaks (all instances)", "analyze.py", "ids = sorted(set(by_arm[first]) & set(by_arm[second]))",
     "ids = sorted(set(by_arm[first]))"),
    ("wins and losses swapped", "analyze.py", 'wins = sum(1 for i in ids if a[i]["passed"] and not b[i]["passed"])',
     'wins = sum(1 for i in ids if b[i]["passed"] and not a[i]["passed"])'),
    ("decision rule ignores the threshold", "analyze.py", "ALPHA = 0.025", "ALPHA = 1.0"),
    ("tiers pooled", "analyze.py", 't.setdefault((u["model"], u["tier"]), {})', 't.setdefault((u["model"], ""), {})'),
    ("empty reply gets no reason of its own", "rsig.py", '    if not body.strip():\n        return None, "the reply was empty"\n', ""),
    ("unknown mock kind is accepted", "runner.py", "    if kind not in MOCK_KINDS:\n        raise ValueError(kind)\n", "    pass\n"),
    ("decision rule: floor is exclusive", "analyze.py", "all(r <= EDGE for r in rates)", "all(r < EDGE for r in rates)"),
    ("decision rule: ceiling is exclusive", "analyze.py", "all(r >= 1 - EDGE for r in rates)", "all(r > 1 - EDGE for r in rates)"),
    ("decision rule: ten discordant pairs are too few", "analyze.py", "< MIN_DISCORDANT:", "<= MIN_DISCORDANT:"),
    ("decision rule: p equal to the threshold is not support", "analyze.py", 'primary["p_pass_sign"] <= ALPHA', 'primary["p_pass_sign"] < ALPHA'),
    ("decision rule: reverse p at the threshold is not against", "analyze.py", 'primary["p_reverse"] <= ALPHA', 'primary["p_reverse"] < ALPHA'),
    ("decision rule: a tie is not against", "analyze.py", 'primary["first_only"] <= primary["second_only"]', 'primary["first_only"] < primary["second_only"]'),
    ("overall ignores a tier against", "analyze.py", 'if "supports" in vs and "against" not in vs:', 'if "supports" in vs:'),
    ("recount reads a colon as the separator", "recount.py", 'line[at] != "=":', 'line[at] not in "=:":'),
    ("recount accepts a dangling slash", "recount.py", "if den is None:\n            return None", "if den is None:\n            den = \"1\""),
    ("recount accepts trailing text", "recount.py", "if at != len(line) or int(den) == 0:", "if int(den) == 0:"),
    ("recount accepts a short assignment", "recount.py", "return values if len(values) == n else None", "return values"),
    ("recount skips the verdict comparison", "recount.py", "if verdict != r[\"verdict\"]:", "if False:"),
    ("recount tail needs more than n lines", "recount.py", "if len(lines) >= n else None", "if len(lines) > n else None"),
    ("recount stops counting decimal answers", "recount.py", "if decimal_answer(r[\"reply\"], n):", "if False:"),
    ("recount stops counting correct decimal answers", "recount.py",
     "closing[\"decimal_answers_that_would_satisfy_every_constraint\"] += 1",
     "closing[\"decimal_answers_that_would_satisfy_every_constraint\"] += 0"),
    ("recount misreads the closing assignment", "recount.py", "all(tail[u] - tail[w] - b <= 0 for _, u, w, b in cons)", "True"),
]


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    return p.returncode


def checks(d):
    flags = ["-O", "-B", "-W", "error"]
    py = sys.executable
    if run([py] + flags + ["-m", "unittest", "discover", "-s", "tests"], d) != 0:
        return "unit tests"
    if run([py] + flags + ["selftest.py"], d) != 0:
        return "selftest"
    if run([py, "-I", "-B", "recount_controls.py"], d) != 0:
        return "recount controls"
    return None


def main():
    survivors = []
    base = tempfile.mkdtemp(prefix="rsig-mut-")
    try:
        d = os.path.join(base, "clean")
        shutil.copytree(HERE, d, ignore=shutil.ignore_patterns("__pycache__", ".git", "texts"))
        if checks(d) is not None:
            print("clean copy is not green")
            return 2
        for i, (name, fn, old, new) in enumerate(MUTATIONS):
            d = os.path.join(base, "m%d" % i)
            shutil.copytree(os.path.join(base, "clean"), d)
            path = os.path.join(d, fn)
            src = open(path).read()
            if src.count(old) != 1:
                print("MUTATION DOES NOT APPLY (%d matches): %s" % (src.count(old), name))
                survivors.append(name)
                continue
            open(path, "w").write(src.replace(old, new))
            red = checks(d)
            print("%-48s %s" % (name, ("red in " + red) if red else "STILL GREEN"))
            if red is None:
                survivors.append(name)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("%d mutations, %d survivors" % (len(MUTATIONS), len(survivors)))
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
