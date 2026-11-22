"""Prints the local-measurement numbers that PREREG.md quotes and that are not
in summary.json: the free-reasoning counts, the time per call and what it
projects for the full plan, and the facts of the two smoke runs and the layout
check, read from the committed logs under logs/.

    python3 -I -B facts.py

Standard library plus the record's own cost.py and driver.py (for the number of
sampling calls of the full plan). Exits 1 if a log does not hold what the plan
quotes. The output is committed as facts.txt.
"""
import json
import os
import re
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.dirname(HERE)
sys.path.insert(0, RECORD)
import cost  # noqa: E402
import driver  # noqa: E402


def read(*parts):
    with open(os.path.join(HERE, *parts), "r", encoding="utf-8") as fh:
        return fh.read()


def two_places(x):
    """A Fraction as a decimal with two places, by integer arithmetic."""
    hundredths = (x * 100 + Fraction(1, 2)).__floor__()
    return "%d.%02d" % (hundredths // 100, hundredths % 100)


def main():
    problems, out = [], []
    rows = [json.loads(ln) for ln in read("results.jsonl").splitlines() if ln.strip()]
    free = [r for r in rows if r["mode"] == "R"]
    forced = [r for r in rows if r["mode"] == "F"]
    out.append("forced-answer calls: %d" % len(forced))
    out.append("free-reasoning calls: %d" % len(free))
    out.append("free-reasoning calls with no thinking tokens: %d" % sum(1 for r in free if r["thinking_tokens"] == 0))
    out.append("free-reasoning fewest thinking tokens in one call: %d" % min(r["thinking_tokens"] for r in free))
    out.append("free-reasoning fewest generated tokens in one call: %d" % min(r["gen_tokens"] for r in free))
    for text in ("B", "C"):
        for tier in ("S", "M"):
            cell = [r for r in free if r["text"] == text and r["tier"] == tier]
            count = lambda name: sum(1 for r in cell if r["outcome"] == name)
            out.append("free %s tier %s: %d calls, passed %d, no answer %d, cut by the cap %d" % (
                text, tier, len(cell), count("passed"), count("no_answer"), count("cut")))
    summary = json.loads(read("summary.json"))
    mean_ms = summary["seconds_per_call_ms"]["F_mean"]
    free_ms = summary["seconds_per_call_ms"]["R_mean"]
    out.append("mean milliseconds per call, forced answer: %d" % mean_ms)
    out.append("mean milliseconds per call, free reasoning: %d" % free_ms)
    calls, steps = driver.plan_calls(cost.full_plan(2048, 2, 96))
    hours = Fraction(mean_ms * calls, 1000 * 3600)
    out.append("sampling calls of the full plan: %d, training steps: %d" % (calls, steps))
    out.append("hours of sampling for the full plan at the local mean per call: %s (%s)" % (two_places(hours), hours))
    out.append("that is above the 12 hour gate: %s" % ("yes" if hours > driver.PILOT_MAX_HOURS else "no"))

    smoke = read("logs", "smoke.out")
    smoke2 = read("logs", "smoke2.out")
    stdout = read("logs", "baseline-stdout.txt")
    # one line per try: finish length, 96 tokens, an empty content
    empty96 = (len(re.findall(r"finish: length \| usage: \{'completion_tokens': 96,.*\n.*\ncontent: ''", smoke))
               + len(re.findall(r"finish: length \| completion_tokens: 96 \|.*content: ''", smoke2)))
    out.append("tries at a cap of 96 with an empty answer (smoke.out, then smoke2.out A to D): %d" % empty96)
    reasoned = (sum(1 for n in re.findall(r"^reasoning_len: (\d+)$", smoke, re.M) if int(n) > 0)
                + sum(1 for n in re.findall(r"reasoning chars: (\d+) \|", smoke2) if int(n) > 0))
    out.append("calls of the two smoke runs that returned reasoning text: %d" % reasoned)
    m = re.search(r"finish: stop \| usage: \{'completion_tokens': (\d+),.*\n.*\ncontent: '([^']*)'", smoke)
    out.append("one-line arithmetic question: %s completion tokens, answer %r" % (m.group(1), m.group(2)) if m else "MISSING")
    m = re.search(r"E default, cap 1500\nfinish: stop \| completion_tokens: (\d+) \|", smoke2)
    out.append("puzzle at a cap of 1500: %s completion tokens, finished" % m.group(1) if m else "MISSING")
    m = re.search(r"layout equals codec.py ids on (\d+) prompts", stdout)
    out.append("local layout equals codec.py ids on %s prompts" % m.group(1) if m else "MISSING")
    for line in out:
        if line == "MISSING" or line.endswith("MISSING"):
            problems.append("a log does not hold the line the plan quotes")
    print("\n".join(out))
    for p in problems:
        print("PROBLEM: " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
