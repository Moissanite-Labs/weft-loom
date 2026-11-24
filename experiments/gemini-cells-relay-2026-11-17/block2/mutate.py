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
COPY = ("referee", "seed", "tests")

UNITS = ("test_units.py", None)
OFFLINE = "test_offline.py"
SANDBOX = ("sandbox", None)

# id, file, text to find, replacement, (test file pattern, -k selector or None), what it breaks
MUTATIONS = [
    ("M01", "referee/relay.py", 'return "commit" if cand >= inc - margin else "regress"',
     'return "commit" if cand > inc - margin else "regress"', UNITS, "gate keeps a candidate exactly at the margin"),
    ("M02", "referee/relay.py", 'return "commit" if cand >= inc - margin else "regress"',
     'return "commit" if cand >= inc - 2 * margin else "regress"', UNITS, "gate margin"),
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
    ("M12", "referee/bench.py", '        if out.pop("limit_hit"):\n            self._wait_for_backend()\n            return True',
     '        if out.pop("limit_hit") and False:\n            self._wait_for_backend()\n            return True',
     (OFFLINE, "usage_limit"), "an episode cut short by the usage limit is rerun"),
    ("M13", "referee/bench.py", "            if reruns < self.hard_cap_reruns:", "            if False:",
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
     '        or body.isascii():\n        return int(body)', UNITS, "decode accepts ASCII digits only"),
    ("M25", "referee/tasks/_util.py", '    if tag == "b" and type(body) is bool:',
     '    if tag == "b":', UNITS, "decode type checks"),
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
            shutil.copytree(HERE / name, baseline / name, ignore=shutil.ignore_patterns("__pycache__"))
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
