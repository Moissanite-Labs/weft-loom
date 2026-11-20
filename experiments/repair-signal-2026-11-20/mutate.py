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
FILES = ["rsig.py", "runner.py", "analyze.py", "stats.py", "selftest.py"]

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
    return None


def main():
    survivors = []
    base = tempfile.mkdtemp(prefix="rsig-mut-")
    try:
        d = os.path.join(base, "clean")
        shutil.copytree(HERE, d, ignore=shutil.ignore_patterns("__pycache__", ".git", "texts", "*.jsonl", "results"))
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
