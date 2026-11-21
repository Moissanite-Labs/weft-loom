"""Independent recount of a registered run. Written after the first run. Not part of the registered analysis.

It shares no code with the harness (rsig.py, runner.py, stats.py, analyze.py). It reads the constraints from the logged
prompt text, parses each logged reply with its own parser written from the reply format in PREREG.md and rsig.py's
docstring, rebuilds every verdict and every violation with exact fractions, and recounts the arms. Any disagreement
with a logged verdict stops the script with a non-zero exit. recount_controls.py checks the two parsers against each
other on generated replies.

Part 1 of the output repeats the registered counts, so it can be compared with analyze.py.
Part 2 is descriptive and was not preregistered: what follows an unreadable reply, per arm.

Usage: python3 -I -B recount.py results/NAME-S.jsonl results/NAME-M.jsonl
"""
import json
import re
import sys
from fractions import Fraction
from math import comb
from statistics import median

K = 4
ARMS = "ABCD"
CONSTRAINT = re.compile(r"^(\w+): x(\d+) - x(\d+) <= (-?\d+(?:/\d+)?)$")
DIGITS = "0123456789"
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
VARIABLES = re.compile(r"x0 to x(\d+)")


def stop(message):
    raise SystemExit("RECOUNT_FAIL: " + message)


def read_constraints(prompt):
    found = []
    for line in prompt.splitlines():
        m = CONSTRAINT.match(line.strip())
        if m:
            found.append((m.group(1), int(m.group(2)), int(m.group(3)), Fraction(m.group(4))))
    if not found:
        stop("no constraints in a first prompt")
    return found


def take_digits(text, at, most):
    """Read 1 to `most` ASCII digits starting at `at`. Returns (digits, next position) or (None, at)."""
    end = at
    while end < len(text) and text[end] in DIGITS:
        end += 1
    if end == at or end - at > most:
        return None, at
    return text[at:end], end


def read_line(line):
    """'xI = p' or 'xI = p/q' with optional spaces or tabs around '=', ASCII digits, at most 12 digits per number."""
    if not line.startswith("x"):
        return None
    index, at = take_digits(line, 1, len(line))
    if index is None or (len(index) > 1 and index[0] == "0"):
        return None
    while at < len(line) and line[at] in " \t":
        at += 1
    if at >= len(line) or line[at] != "=":
        return None
    at += 1
    while at < len(line) and line[at] in " \t":
        at += 1
    sign = 1
    if at < len(line) and line[at] == "-":
        sign, at = -1, at + 1
    num, at = take_digits(line, at, 12)
    if num is None:
        return None
    den = "1"
    if at < len(line) and line[at] == "/":
        den, at = take_digits(line, at + 1, 12)
        if den is None:
            return None
    if at != len(line) or int(den) == 0:
        return None
    return int(index), Fraction(sign * int(num), int(den))


def inside_fence(body):
    """If the whole reply is one code fence, return what is inside it. Otherwise return the reply unchanged."""
    if not (body.startswith("```") and body.endswith("```")):
        return body
    newline = body.find("\n")
    if newline < 0 or newline + 1 + 3 > len(body) or any(ch not in LETTERS for ch in body[3:newline]):
        return body
    inner = body[newline + 1:-3]
    return inner[:-1] if inner.endswith("\n") else inner


def read_lines(lines, n):
    values = {}
    for line in lines:
        got = read_line(line)
        if got is None or got[0] >= n or got[0] in values:
            return None
        values[got[0]] = got[1]
    return values if len(values) == n else None


def read_reply(reply, n):
    """The registered reply format: only assignment lines, one per variable, optionally inside one code fence.
    Blank lines are skipped. Anything else makes the reply unreadable (None)."""
    body = inside_fence(reply.strip())
    lines = [line.strip() for line in body.split("\n")]
    return read_lines([line for line in lines if line], n)


def closing_assignment(reply, n):
    """For an unreadable reply: do its last n non-blank lines form a complete assignment? Returns it or None."""
    lines = [line.strip() for line in reply.strip().split("\n")]
    lines = [line for line in lines if line and line != "```"]
    return read_lines(lines[-n:], n) if len(lines) >= n else None


DECIMAL_LINE = re.compile(r"^x[0-9]+[ \t]*=[ \t]*-?[0-9]+(?:\.[0-9]+)?(?:/[0-9]+)?$", re.ASCII)


def decimal_answer(reply, n):
    """Is this unreadable reply a plain list of n assignments in which at least one number has a decimal point?"""
    lines = [line.strip() for line in reply.strip().split("\n") if line.strip()]
    return len(lines) == n and all(DECIMAL_LINE.match(line) for line in lines) and any("." in line for line in lines)


def sign_p(first_only, second_only):
    """Exact one-sided binomial sign test: chance of at least first_only heads in first_only + second_only fair flips."""
    n = first_only + second_only
    if n == 0:
        return 1.0
    return sum(comb(n, i) for i in range(first_only, n + 1)) / 2 ** n


def recount(path):
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    unit_rows = [r for r in rows if r["type"] == "unit"]
    units = {(r["arm"], r["instance"]): r for r in unit_rows}
    if len(unit_rows) != 400 or len(units) != 400:
        stop(f"{path}: expected 400 distinct units, found {len(unit_rows)} lines and {len(units)} keys")
    instances = sorted({i for _, i in units})
    if len(instances) != 100 or instances != list(range(instances[0], instances[0] + 100)):
        stop(f"{path}: instances are not 100 consecutive seeds")
    if any((a, i) not in units for a in ARMS for i in instances):
        stop(f"{path}: an arm is missing an instance")
    by_unit = {}
    for r in rows:
        if r["type"] == "round":
            by_unit.setdefault((r["arm"], r["instance"]), []).append(r)
    if set(by_unit) != set(units):
        stop(f"{path}: round lines and unit lines name different units")

    solved, rounds_to, first = {}, {}, {}
    requests, seconds = 0, 0.0
    unreadable = {a: [0, 0] for a in ARMS}
    repeats = {a: [0, 0] for a in ARMS}
    after_unreadable = {a: [0, 0] for a in ARMS}
    after_readable_fail = {a: [0, 0] for a in ARMS}
    unreadable_in_round_2 = {a: 0 for a in ARMS}
    solved_by_round = {a: [0] * K for a in ARMS}
    seconds_unreadable, seconds_readable = [], []
    closing = {"unreadable": 0, "by_round": [0] * K, "answers_written_with_a_decimal": 0,
               "end_in_complete_assignment": 0, "that_assignment_satisfies_every_constraint": 0,
               "next_round_passes_after_one_ending_in_an_assignment": [0, 0], "next_round_passes_after_one_that_does_not": [0, 0]}

    for (arm, inst), rs in by_unit.items():
        rs.sort(key=lambda r: r["round"])
        if [r["round"] for r in rs] != list(range(1, len(rs) + 1)) or len(rs) > K:
            stop(f"{path}: rounds of {arm} {inst} are not 1..n with n <= {K}")
        cons = read_constraints(rs[0]["prompt"])
        n = int(VARIABLES.search(rs[0]["prompt"]).group(1)) + 1
        for j in range(1, len(rs)):
            if rs[j]["prompt"] != rs[j - 1]["feedback"]:
                stop(f"{path}: {arm} {inst} round {j + 1} was not sent the feedback logged for round {j}")
        passed_at = None
        mine = []
        for r in rs:
            requests += 1
            seconds += r["seconds"]
            values = read_reply(r["reply"], n)
            unreadable[arm][1] += 1
            if values is None:
                verdict = "unparsable"
                unreadable[arm][0] += 1
                seconds_unreadable.append(r["seconds"])
                if r["round"] == 2:
                    unreadable_in_round_2[arm] += 1
                if r["parse_error"] is None:
                    stop(f"{path}: {arm} {inst} round {r['round']} is unreadable here but was read by the harness")
            else:
                if r["parse_error"] is not None:
                    stop(f"{path}: {arm} {inst} round {r['round']} is readable here but not by the harness")
                seconds_readable.append(r["seconds"])
                excess = sorted((c, str(values[u] - values[w] - b)) for c, u, w, b in cons if values[u] - values[w] - b > 0)
                verdict = "pass" if not excess else "fail"
                logged = sorted((v["cid"], v["excess"]) for v in (r["violations"] or []))
                if excess != logged:
                    stop(f"{path}: {arm} {inst} round {r['round']} violations differ from the log")
            if verdict != r["verdict"]:
                stop(f"{path}: {arm} {inst} round {r['round']} verdict {verdict} here, {r['verdict']} in the log")
            if (r["feedback"] is None) != (verdict == "pass"):
                stop(f"{path}: {arm} {inst} round {r['round']} feedback and verdict disagree")
            if verdict == "pass" and passed_at is None:
                passed_at = r["round"]
            mine.append((verdict, values))
        if passed_at is not None and passed_at != len(rs):
            stop(f"{path}: {arm} {inst} kept going after a pass")
        if passed_at is None and len(rs) != K:
            stop(f"{path}: {arm} {inst} stopped early without a pass")
        unit = units[(arm, inst)]
        if unit["passed"] != (passed_at is not None) or unit["pass_round"] != passed_at:
            stop(f"{path}: unit line of {arm} {inst} disagrees with its rounds")
        for j, r in enumerate(rs):
            if mine[j][0] != "unparsable":
                continue
            closing["unreadable"] += 1
            closing["by_round"][r["round"] - 1] += 1
            closing["answers_written_with_a_decimal"] += decimal_answer(r["reply"], n)
            tail = closing_assignment(r["reply"], n)
            if tail is not None:
                closing["end_in_complete_assignment"] += 1
                closing["that_assignment_satisfies_every_constraint"] += all(tail[u] - tail[w] - b <= 0 for _, u, w, b in cons)
            if j + 1 < len(mine):
                key = "next_round_passes_after_one_ending_in_an_assignment" if tail is not None else "next_round_passes_after_one_that_does_not"
                closing[key][1] += 1
                closing[key][0] += mine[j + 1][0] == "pass"
        for j in range(1, len(mine)):
            repeats[arm][1] += 1
            both_readable = mine[j][1] is not None and mine[j - 1][1] is not None
            both_unreadable = mine[j][1] is None and mine[j - 1][1] is None
            # The harness counts a repeat when two readable answers have equal values, and also when two unreadable
            # replies are the same text. The recount follows it.
            if (both_readable and mine[j][1] == mine[j - 1][1]) or (both_unreadable and rs[j]["reply"] == rs[j - 1]["reply"]):
                repeats[arm][0] += 1
            bucket = after_unreadable if mine[j - 1][0] == "unparsable" else after_readable_fail
            bucket[arm][1] += 1
            bucket[arm][0] += mine[j][0] == "pass"
        solved[(arm, inst)] = passed_at is not None
        rounds_to[(arm, inst)] = passed_at if passed_at else K + 1
        if passed_at:
            solved_by_round[arm][passed_at - 1] += 1
        first[(arm, inst)] = rs[0]["reply"]

    same_first = sum(1 for i in instances if len({first[(a, i)] for a in ARMS}) == 1)
    out = {
        "file": path,
        "registered_counts": {
            "requests": requests,
            "hours_inside_requests": round(seconds / 3600, 2),
            "solved_of_100": {a: sum(solved[(a, i)] for i in instances) for a in ARMS},
            "solved_in_round_1_to_4": solved_by_round,
            "first_reply_identical_in_all_four_arms": same_first,
            "unreadable_rounds": {a: "%d/%d" % tuple(unreadable[a]) for a in ARMS},
            "repeated_answers": {a: "%d/%d" % tuple(repeats[a]) for a in ARMS},
        },
        "not_preregistered": {
            "unreadable_replies_in_round_2": unreadable_in_round_2,
            "next_round_passes_after_unreadable_round": {a: "%d/%d" % tuple(after_unreadable[a]) for a in ARMS},
            "next_round_passes_after_readable_failed_round": {a: "%d/%d" % tuple(after_readable_fail[a]) for a in ARMS},
            "median_seconds_per_unreadable_reply": round(median(seconds_unreadable), 1) if seconds_unreadable else None,
            "median_seconds_per_readable_reply": round(median(seconds_readable), 1) if seconds_readable else None,
            "unreadable_replies": {k: ("%d/%d" % tuple(v) if isinstance(v, list) and len(v) == 2 else v)
                                   for k, v in closing.items()},
        },
    }
    for name, x, y in (("primary_C_vs_B", "C", "B"), ("check_B_vs_A", "B", "A"), ("check_C_vs_D", "C", "D")):
        a = sum(1 for i in instances if solved[(x, i)] and not solved[(y, i)])
        b = sum(1 for i in instances if solved[(y, i)] and not solved[(x, i)])
        out["registered_counts"][name] = {"first_only": a, "second_only": b, "p_first": sign_p(a, b), "p_second": sign_p(b, a)}
    return out


def main(argv):
    if not argv:
        stop("give one or more run logs")
    print(json.dumps([recount(p) for p in argv], indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
