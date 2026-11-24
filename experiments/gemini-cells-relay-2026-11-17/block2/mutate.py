#!/usr/bin/env python3
"""Mutation check of the referee's guards: each guard is removed or weakened, one at a
time, in a scratch copy of the record, and the tests named beside it must then fail.

Run from the record folder, as root on Linux (the sandbox tests need it):

    python3 -I -B block2/mutate.py            # all mutations
    python3 -I -B block2/mutate.py M03 M17    # only these

Prints one line per mutation and exits nonzero if any survives or does not apply. Each
mutation's text must occur exactly once in its file, so a guard that moves breaks this
script instead of being skipped silently. No model is called.
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent.parent
COPY = ("referee", "seed", "tests", "block2", "results", "run.py")

UNITS = ("test_units.py", None)
OFFLINE = "test_offline.py"
SANDBOX = ("sandbox", None)

# id, file, text to find, replacement, (test file pattern, -k selector or None), what it breaks
MUTATIONS = [
    ("M01", "referee/relay.py", 'return "commit" if round(cand - inc, 9) >= -margin else "regress"',
     'return "commit" if round(cand - inc, 9) > -margin else "regress"', UNITS, "gate keeps a candidate exactly at the margin"),
    ("M02", "referee/relay.py", 'return "commit" if round(cand - inc, 9) >= -margin else "regress"',
     'return "commit" if round(cand - inc, 9) >= -2 * margin else "regress"', UNITS, "gate margin"),
    ("M03", "referee/relay.py", 'd = hashlib.sha256(f"{key}|{t}|{fam}|{i}".encode()).digest()',
     'd = hashlib.sha256(f"{t}|{fam}|{i}".encode()).digest()', UNITS, "instance seeds depend on the key"),
    ("M04", "referee/relay.py", 'inst = instances(f"{self.secret}|{cand_h}", t, c.families, c.per_family)',
     'inst = instances(f"{self.secret}", t, c.families, c.per_family)', (OFFLINE, "commit_then_reveal"),
     "seeds are drawn after the candidate is fixed"),
    ("M05", "referee/relay.py", '            if not boot["ok"]:\n                ev.update(outcome="boot_fail"',
     '            if False:\n                ev.update(outcome="boot_fail"', (OFFLINE, "boot_failure"),
     "a candidate that does not boot is discarded"),
    ("M06", "referee/bench.py", "    elif size > max_bytes:", "    elif size > max_bytes * 10:",
     (OFFLINE, "surface_cap"), "harness size cap"),
    ("M07", "referee/bench.py", '    if not (Path(root) / "agent.py").is_file():', "    if False:",
     (OFFLINE, "surface_cap"), "a harness must have agent.py"),
    ("M08", "referee/bench.py", '        sandbox.strip_symlinks(ep / "work")\n        return {"rc": rc,',
     '        return {"rc": rc,', (OFFLINE, "symlink"), "symlinks in work are removed before scoring"),
    ("M09", "referee/brain.py", "            if self.used >= self.calls:", "            if self.used > self.calls:",
     UNITS, "call cap"),
    ("M10", "referee/brain.py", 'prompt, clipped = clip_middle(str(req.get("prompt", "")), self.prompt_chars)',
     'prompt, clipped = str(req.get("prompt", "")), False', UNITS, "prompt clipping in the server"),
    ("M11", "referee/brain.py", 'system = str(req.get("system", ""))[:8000]', 'system = str(req.get("system", ""))',
     UNITS, "system prompt cap"),
    ("M12", "referee/bench.py", '        if out.pop("limit_hit"):\n            state["attempts"].append(',
     '        if out.pop("limit_hit") and False:\n            state["attempts"].append(',
     (OFFLINE, "usage_limit"), "an episode cut short by the usage limit is rerun"),
    ("M13", "referee/bench.py", '            if state["reruns"] < self.hard_cap_reruns:', "            if False:",
     (OFFLINE, "hard_cap"), "a hard-cap kill is rerun"),
    ("M14", "referee/bench.py", '            out["referee_fault"] = True', "            pass",
     (OFFLINE, "hard_cap"), "a result after the last rerun is flagged as a referee fault"),
    ("M15", "referee/sandbox.py", "        elif own_limit and elapsed - waited >= own_limit[0]:",
     "        elif own_limit and elapsed >= own_limit[0]:", (OFFLINE, "slow_model"),
     "model wait is not charged to the cell"),
    ("M16", "referee/bench.py", "own_limit=(wall_s, srv.model_wait_s),", "own_limit=None,",
     (OFFLINE, "own_time"), "the cell's own time is limited"),
    ("M17", "referee/brain.py", "                self._wait_s += time.monotonic() - self._busy_since",
     "                pass", (OFFLINE, "slow_model"), "model wait is counted"),
    ("M18", "referee/tasks/spec.py",
     '        return json.dumps(value, sort_keys=True) == json.dumps(case["value"], sort_keys=True)',
     "        return True", UNITS, "spec compares each value with the expected one"),
    ("M19", "referee/tasks/bugfix.py", "        return (value == eval(expected, {})) is True",
     "        return True", UNITS, "bugfix compares each value with the expected one"),
    ("M20", "referee/tasks/_util.py", '        if not isinstance(record, dict) or record.get("nonce") != nonce:',
     "        if not isinstance(record, dict):", UNITS, "the result line must carry the nonce"),
    ("M21", "referee/tasks/_util.py", "        if type(results) is not list or len(results) != count or count <= 0:",
     "        if type(results) is not list or count <= 0:", UNITS, "the result line must cover every call"),
    ("M22", "referee/tasks/_util.py", '    return type(outcome) is dict and outcome == {"x": "ValueError"}',
     '    return type(outcome) is dict and "x" in outcome', UNITS, "only ValueError counts as raising it"),
    ("M23", "referee/tasks/_util.py", "    if depth > MAX_DEPTH:\n        raise ValueError(\"too deep\")",
     "    if False:\n        raise ValueError(\"too deep\")", UNITS, "decode depth limit"),
    ("M24", "referee/tasks/_util.py", '        and body.isascii():\n        return int(body)',
     '        or body.isascii():\n        return int(body)', UNITS, "decode accepts ASCII digits only (hygiene, not security)"),
    ("M25", "referee/tasks/_util.py", '    if tag == "b" and type(body) is bool:',
     '    if tag == "b":', UNITS, "decode type checks (hygiene, not security)"),
    ("M26", "referee/tasks/_util.py", '        if type(outcome) is dict and set(outcome) == {"v"}:',
     '        if type(outcome) is dict and "v" in outcome:', UNITS, "an outcome is a value or a marker, not both"),
    ("M27", "referee/relay.py", 'builder_h = seed_h if s["builder"] == "seed" else H[me]',
     "builder_h = H[me]", (OFFLINE, "fixed_builder"),
     "the fixed-builder control builds in the seed"),
    ("M28", "referee/sandbox.py", '"--mount", "--net", "--pid"', '"--mount", "--pid"', SANDBOX,
     "the sandbox has no network"),
    ("M29", "referee/sandbox.py", '"/tmp", "/srv", "/mnt"', '"/tmp", "/mnt"', SANDBOX,
     "the referee's run tree is masked"),
    ("M30", "referee/brain.py", '        if self._locked(lambda d: d.get("usd", 0.0)) >= self.cap:',
     "        if False:", (OFFLINE, "spend_cap"), "spend cap"),
    ("M31", "referee/tasks/bugfix.py", '        modules = [{"module": item["spec"], "exprs": [expr for expr, _ in item["tests"]]}',
     '        modules = [{"module": item["spec"], "exprs": [expr for expr, _ in item["tests"]], "tests": item["tests"]}',
     UNITS, "the bugfix hidden script holds no expected result"),
    ("M32", "referee/tasks/spec.py", '        body = f"FUNC = {truth[\'func\']!r}\\nCALLS = json.loads({json.dumps(calls)!r})\\n" + TEST_BODY',
     '        body = f"FUNC = {truth[\'func\']!r}\\nCALLS = json.loads({json.dumps(calls)!r})\\nTESTS = {tests!r}\\n" + TEST_BODY',
     UNITS, "the spec hidden script holds no expected result"),
    ("M33", "referee/tasks/_util.py", "        if stdout is None or len(stdout) > MAX_STDOUT_BYTES:",
     "        if stdout is None:", UNITS, "the referee refuses an oversized hidden-run output"),
    ("M34", "referee/bench.py", ' | head -c {_util.MAX_STDOUT_BYTES + 1}"]', '"]', (OFFLINE, "real_sandbox"),
     "the referee reads a bounded amount of a hidden run's output"),
    ("M35", "referee/tasks/_util.py", '    if tag in ("l", "t") and type(body) is list:',
     '    if tag in ("l", "t", "S", "F") and type(body) is list:', UNITS, "decode builds no sets (hash flooding)"),
    ("M36", "referee/brain.py", "        if not prompt.strip():", "        if False:", UNITS,
     "an empty prompt is refused without a model call"),
    ("M37", "referee/brain.py", "        finally:\n            self._leave_call()", "        finally:\n            pass",
     UNITS, "a failed call stops the wait clock"),
    ("M38", "referee/bench.py", '            state["limit_reruns"] += 1', '            state["reruns"] += 1', UNITS,
     "usage-limit reruns do not use up hard-limit reruns"),
    ("M39", "referee/relay.py", 'return "commit" if round(cand - inc, 9) >= -margin else "regress"',
     'return "commit" if cand >= inc - margin else "regress"', UNITS, "gate is exact at the margin"),
    ("M40", "run.py", '    if root is not None and approval.get("root") != str(Path(root).resolve()):',
     "    if False:", UNITS, "an approval is bound to one root, so one ledger"),
    ("M41", "run.py", '        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != want:',
     "        if False:", UNITS, "frozen files must match the plan's hashes"),
    ("M42", "run.py", "    cap = check_approval(a.approval, a.tag, a.root)", "    cap = 50.0", UNITS,
     "assay2 checks the approval before any backend exists"),
    ("M43", "referee/relay.py", '"model_errors", "timed_out", "model_wait_s",\n                                               "reruns", "limit_reruns", "referee_fault")}',
     '"model_errors")}', (OFFLINE, "twin_commit"), "boot faults reach the turn row"),
    ("M44", "block2/analyze_a.py", '    if row.get("build_referee_fault") or (row.get("boot") or {}).get("referee_fault"):',
     "    if False:", UNITS, "the analysis leaves out referee faults"),
    ("M45", "run.py", "        random.Random(f\"{ORDER_SEED}|{tag}|{rep}\").shuffle(rows)", "        pass", UNITS,
     "part A's order is shuffled within each repeat"),
]


def run_tests(root, tests):
    pattern, selector = tests
    if pattern == "sandbox":
        cmd = [sys.executable, "-I", "-B", str(root / "tests" / "sandbox_selftest.py")]
    else:
        cmd = [sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", pattern]
        if selector:
            cmd += ["-k", selector]
    try:
        done = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "caught" if done.returncode != 0 else "SURVIVED"


def main(argv):
    chosen = [m for m in MUTATIONS if not argv or m[0] in argv]
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="gc-mutate-", dir="/srv"))
    bad = 0
    try:
        # Same depth below a repository-like root as the real record, because the sandbox
        # self-test finds "the repository" three folders above its own file.
        baseline = scratch / "base" / "experiments" / "record"
        baseline.mkdir(parents=True)
        for name in COPY:
            if (HERE / name).is_dir():
                shutil.copytree(HERE / name, baseline / name, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(HERE / name, baseline / name)
        patterns = sorted({m[4] for m in chosen}, key=str)
        for tests in patterns:
            if run_tests(baseline, tests) != "SURVIVED":  # i.e. the unmutated copy passes
                print(f"baseline fails for {tests}: fix the tests first")
                return 2
        for mid, rel, old, new, tests, what in chosen:
            work = scratch / mid / "experiments" / "record"
            shutil.copytree(baseline, work)
            path = work / rel
            text = path.read_text()
            if text.count(old) != 1:
                print(f"{mid}  NOT APPLIED  ({text.count(old)} matches in {rel})  {what}")
                bad += 1
                continue
            path.write_text(text.replace(old, new))
            # Re-freeze the plan in the mutant copy, so that the test of the plan's hashes does
            # not catch every mutation by itself: only the tests named beside it should.
            subprocess.run([sys.executable, "-I", "-B", str(work / "block2" / "freeze.py")], cwd=work,
                           check=True, capture_output=True)
            started = time.monotonic()
            verdict = run_tests(work, tests)
            label = tests[0] + (f" -k {tests[1]}" if tests[1] else "")
            print(f"{mid}  {verdict:8}  {time.monotonic() - started:5.1f}s  {rel:26} {what}  [{label}]")
            bad += verdict != "caught"
            shutil.rmtree(scratch / mid, ignore_errors=True)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print(f"\n{len(chosen)} mutations, {len(chosen) - bad} caught, {bad} not caught or not applied")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
