#!/usr/bin/env python3
"""Self-test of the task families. Run as `python3 selftest.py` from any directory
(`python3 selftest.py --seeds N` tests seeds 0..N-1 instead of the default 0..59).

For every family, seeds 0..59 and levels 1..3 it checks that
  (a) an empty workdir, and the fresh instance without an answer, score exactly 0.0
      (for bugfix the untouched buggy package must score strictly between 0.2 and 0.8);
  (b) solve_from_files, which reads only the instance files, scores exactly 1.0;
  (c) the careless sloppy_solve never scores 1.0 and has a level 2 mean strictly between
      0.15 and 0.85;
  (d) generation is deterministic (two runs byte-identical, also in a second process with
      another hash seed) and different seeds give different instances;
  (e) the size limits hold (instance < 60 KB, TASK.md < 2500 chars, other .md < 4000);
  (f) the truth does not appear verbatim in any instance file (data families), the
      example/ folder is consistent with its expected.json, and no code family ships its
      own solution;
plus pool sanity checks and checker robustness against garbage answers. Prints a table
and exits nonzero on any failure.
"""

import hashlib
import importlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
tasks = importlib.import_module(HERE.name)

SEEDS = range(int(sys.argv[2]) if sys.argv[1:2] == ["--seeds"] else 60)
LEVELS = (1, 2, 3)
DATA = ("ledger", "logwin", "stock")
RUN = tasks.local_run_py
FAILURES = []


def fail(where, message):
    FAILURES.append(f"{where}: {message}")


def snapshot(root):
    """Relative path -> bytes for every file under root."""
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def digest(files):
    h = hashlib.sha256()
    for name, blob in sorted(files.items()):
        h.update(name.encode() + b"\0" + hashlib.sha256(blob).digest())
    return h.hexdigest()


def generate(module, seed, level, root):
    """Generate into a new folder under root; return (folder, truth, seconds)."""
    folder = pathlib.Path(tempfile.mkdtemp(dir=root))
    started = time.perf_counter()
    truth = module.generate(seed, folder, level)
    return folder, truth, time.perf_counter() - started


def timed_check(module, folder, truth, timings):
    started = time.perf_counter()
    score = module.check(folder, truth, RUN)
    timings.append(time.perf_counter() - started)
    return score


def size_problems(files):
    problems = []
    total = sum(len(blob) for blob in files.values())
    if total >= 60_000:
        problems.append(f"instance is {total} bytes")
    for name, blob in files.items():
        chars = len(blob.decode("utf-8"))
        if name == "TASK.md" and chars >= 2500:
            problems.append(f"TASK.md has {chars} chars")
        elif name.endswith(".md") and name != "TASK.md" and chars >= 4000:
            problems.append(f"{name} has {chars} chars")
    return problems


def leak_problems(answer, files):
    """Serialisations of the truth, whole or per key, that occur in an instance file."""
    needles = set()
    for sort_keys in (False, True):
        for separators in (None, (",", ":")):
            for indent in (None, 1, 2, 4):
                needles.add(json.dumps(answer, sort_keys=sort_keys, separators=separators, indent=indent))
            for key, value in answer.items():
                colon = ": " if separators is None else ":"
                needles.add(json.dumps(key) + colon + json.dumps(value, sort_keys=sort_keys, separators=separators))
    texts = {name: blob.decode("utf-8") for name, blob in files.items()}
    return [f"truth text found in {name}" for name, text in texts.items()
            if any(needle in text for needle in needles)]


def check_example(module, folder, root):
    """The example/ folder must be a real test: the reference solver reproduces its
    expected.json from the instance rules and the sloppy solver does not."""
    trial = pathlib.Path(tempfile.mkdtemp(dir=root))
    shutil.copy(folder / "FORMAT.md", trial / "FORMAT.md")
    shutil.copytree(folder / "example" / "data", trial / "data")
    expected = {"answer": json.loads((folder / "example" / "expected.json").read_text())}
    module.sloppy_solve(trial)
    careless = module.check(trial, expected, RUN)
    module.solve_from_files(trial)
    return module.check(trial, expected, RUN) == 1.0 and careless < 1.0 and len(expected["answer"]) >= 2


def structure_problems(name, level, folder, truth):
    """Family-specific shape checks of one instance."""
    problems = []
    if name == "bugfix":
        spec_text = (folder / "SPEC.md").read_text()
        if len(truth["modules"]) != (4 if level >= 3 else 3):
            problems.append("wrong number of modules")
        for item in truth["modules"]:
            if not 8 <= len(item["tests"]) <= 12:
                problems.append(f"{item['spec']} has {len(item['tests'])} hidden assertions")
            section = spec_text.split(f"## `pkg/{item['spec']}.py`")[1].split("\n## ")[0]
            shown = section.split("Currently wrong")[0].count("\n    ")
            if not 2 <= shown <= 3:
                problems.append(f"{item['spec']} shows {shown} examples")
            if (folder / "pkg" / f"{item['spec']}.py").read_text() == tasks.bugfix.POOL[item["spec"]]["source"]:
                problems.append(f"{item['spec']} was written without its bug")
    if name == "spec":
        if not 12 <= len(truth["tests"]) <= 16:
            problems.append(f"{len(truth['tests'])} hidden assertions")
        if (folder / "SPEC.md").read_text().split("## Worked examples")[1].count("\n    ") != 3:
            problems.append("SPEC.md does not show 3 worked examples")
        if (folder / "solution.py").exists():
            problems.append("instance ships a solution.py")
    return problems


RULE_KEYS = {
    "ledger": ("delim", "columns", "ts", "excluded", "style", "base", "direction", "rounding"),
    "logwin": ("sep", "order", "ts", "levels", "comment", "end_inclusive", "files"),
    "stock": ("fields", "ship_rule", "dup_rule"),
}


def rule_signature(name, truth):
    """The rule parameters of an instance (without its data) as a comparable string."""
    if name == "bugfix":
        return json.dumps([[item["spec"], item["bug"]] for item in truth["modules"]])
    if name == "spec":
        return json.dumps([truth["spec"], truth["params"]], sort_keys=True)
    return json.dumps([truth["params"][key] for key in RULE_KEYS[name]], sort_keys=True)


def run_cell(name, level, root):
    """All per-instance checks for one (family, level); returns the table row."""
    module = tasks.FAMILIES[name]
    where = f"{name} L{level}"
    sloppy, unfixed, sizes, digests, rules, gen_s, check_s = [], [], [], [], set(), [], []
    for seed in SEEDS:
        tag = f"{where} seed {seed}"
        folder, truth, seconds = generate(module, seed, level, root)
        gen_s.append(seconds)
        files = snapshot(folder)
        twin, truth_again, _ = generate(module, seed, level, root)
        if snapshot(twin) != files or truth_again != truth:
            fail(tag, "generation is not deterministic")
        if json.loads(json.dumps(truth)) != truth:
            fail(tag, "truth does not survive a JSON round trip")
        digests.append(digest(files))
        sizes.append(sum(len(blob) for blob in files.values()))
        rules.add(rule_signature(name, truth))
        for problem in size_problems(files) + structure_problems(name, level, folder, truth):
            fail(tag, problem)
        empty = pathlib.Path(tempfile.mkdtemp(dir=root))
        if module.check(empty, truth, RUN) != 0.0:
            fail(tag, "empty workdir does not score 0.0")
        if name in DATA:
            for problem in leak_problems(truth["answer"], files):
                fail(tag, problem)
            if not check_example(module, folder, root):
                fail(tag, "example/ is not solved by the reference solver, or is solved by the sloppy one")
        if name == "bugfix":
            unfixed.append(timed_check(module, folder, truth, check_s))
            if not 0.2 < unfixed[-1] < 0.8:
                fail(tag, f"unfixed buggy code scores {unfixed[-1]:.3f}")
        elif module.check(folder, truth, RUN) != 0.0:
            fail(tag, "fresh instance without an answer does not score 0.0")
        careless = pathlib.Path(tempfile.mkdtemp(dir=root)) / "work"
        shutil.copytree(folder, careless)
        module.sloppy_solve(careless)
        sloppy.append(timed_check(module, careless, truth, check_s))
        if not 0.0 <= sloppy[-1] < 1.0:
            fail(tag, f"sloppy solver scores {sloppy[-1]:.3f}")
        module.solve_from_files(folder)
        solved = timed_check(module, folder, truth, check_s)
        if solved != 1.0:
            fail(tag, f"reference solver scores {solved:.3f}")
    mean = sum(sloppy) / len(sloppy)
    if level == 2 and not 0.15 < mean < 0.85:
        fail(where, f"sloppy mean {mean:.3f} is outside (0.15, 0.85)")
    if len(set(digests)) != len(digests):
        fail(where, f"only {len(set(digests))} distinct instances for {len(digests)} seeds")
    if max(gen_s) >= 2.0 or max(check_s) >= 2.0:
        fail(where, f"too slow: generate {max(gen_s):.2f}s, check {max(check_s):.2f}s")
    return {"family": name, "level": level, "sloppy": sloppy, "unfixed": unfixed, "bytes": max(sizes),
            "rules": len(rules), "gen_ms": 1000 * max(gen_s), "check_ms": 1000 * max(check_s),
            "digests": digests[:5]}


def check_pools():
    """Static sanity of the bugfix and spec pools."""
    pool = tasks.bugfix.POOL
    if len(pool) < 10:
        fail("bugfix pool", f"only {len(pool)} specs")
    for name, entry in pool.items():
        where = f"bugfix pool {name}"
        if not all(tasks.bugfix.holds(entry["source"], entry["tests"] + entry["examples"])):
            fail(where, "correct source fails its own tests or examples")
        if len(entry["bugs"]) < 2 or not 2 <= len(entry["examples"]) <= 3:
            fail(where, "needs at least 2 bugs and 2 or 3 examples")
        for bug in range(len(entry["bugs"])):
            source = tasks.bugfix.buggy_source(name, bug)
            broken = tasks.bugfix.holds(source, entry["tests"]).count(False)
            passing_examples = tasks.bugfix.holds(source, entry["examples"]).count(True)
            if broken < 3 or passing_examples < 2:
                fail(where, f"bug {bug}: breaks {broken} tests, {passing_examples} examples still pass")
    if len(tasks.spec.POOL) < 8:
        fail("spec pool", f"only {len(tasks.spec.POOL)} specs")


def expect(where, score, low, high):
    if not (isinstance(score, float) and low <= score <= high):
        fail(where, f"score {score!r} is not a float in [{low}, {high}]")


def check_robustness(root):
    """Garbage answers, garbage truth and a broken run_py must give 0.0, never an exception."""
    deep = "[" * 100_000 + "]" * 100_000
    garbage = {
        "not json": b"{not json", "non utf-8": b"\xff\xfe\x00\x80{}", "list": b"[1, 2, 3]",
        "string": b'"text"', "null": b"null", "number": b"3.5", "empty": b"", "deep": deep.encode(),
        "huge": b" " * 3_000_000 + b"{}", "nan": b'{"a": NaN, "b": Infinity, "c": -Infinity}',
    }
    for name in DATA:
        module = tasks.FAMILIES[name]
        folder, truth, _ = generate(module, 0, 2, root)
        answer = folder / "answer.json"
        for label, blob in garbage.items():
            answer.write_bytes(blob)
            expect(f"{name} garbage {label}", module.check(folder, truth, RUN), 0.0, 0.0)
        junk = [None, True, "7", float("nan"), 10 ** 400, [1], {"errors": "x", "on_hand": None, "x": {}}]
        for index, value in enumerate(junk):
            answer.write_text(json.dumps({key: value for key in truth["answer"]}))
            expect(f"{name} junk value {index}", module.check(folder, truth, RUN), 0.0, 0.0)
        module.solve_from_files(folder)
        good = json.loads(answer.read_text())
        good[sorted(good)[0]] = float("inf")
        good["extra key"] = 1
        answer.write_text(json.dumps(good))
        expect(f"{name} one bad key", module.check(folder, truth, RUN), 0.01, 0.99)
        answer.unlink()
        answer.mkdir()
        expect(f"{name} answer.json is a directory", module.check(folder, truth, RUN), 0.0, 0.0)
        for bad_truth in (None, {}, {"answer": {}}, {"answer": 3}):
            expect(f"{name} bad truth", module.check(folder, bad_truth, RUN), 0.0, 0.0)
    fake = 'print(\'{"passed": 99, "total": 99}\')\nimport os\nos._exit(0)\n'
    hang = "while True:\n    pass\n"
    spec = tasks.FAMILIES["spec"]
    folder, truth, _ = generate(spec, 0, 2, root)
    hang_calls = f"def {truth['func']}(*args):\n    while True:\n        pass\n"
    for label, text in {"syntax error": "def (:\n", "prints a fake result": fake, "hangs on import": hang,
                        "hangs in every call": hang_calls, "no function": "x = 1\n",
                        "exits": "raise SystemExit(0)\n"}.items():
        (folder / "solution.py").write_text(text)
        started = time.perf_counter()
        expect(f"spec {label}", spec.check(folder, truth, RUN), 0.0, 0.0)
        if time.perf_counter() - started > 9.5:
            fail(f"spec {label}", "hidden test did not stay under its timeout")
    (folder / "solution.py").unlink()
    (folder / "solution.py").mkdir()
    expect("spec solution.py is a directory", spec.check(folder, truth, RUN), 0.0, 0.0)
    folder, truth, _ = generate(spec, 1, 2, root)
    spec.solve_from_files(folder)
    expect("spec run_py raises", spec.check(folder, truth, lambda *a: 1 / 0), 0.0, 0.0)
    expect("spec run_py returns junk", spec.check(folder, truth, lambda *a: (0, None)), 0.0, 0.0)
    expect("spec bad truth", spec.check(folder, {}, RUN), 0.0, 0.0)
    bugfix = tasks.FAMILIES["bugfix"]
    folder, truth, _ = generate(bugfix, 0, 2, root)
    base = bugfix.check(folder, truth, RUN)
    first = folder / "pkg" / f"{truth['modules'][0]['spec']}.py"
    for label, text in {"hangs on import": hang, "syntax error": "def (:\n", "exits": "raise SystemExit(0)\n"}.items():
        first.write_text(text)
        expect(f"bugfix module {label}", bugfix.check(folder, truth, RUN), 0.05, base - 0.05)
    first.write_text(fake)
    expect("bugfix module prints a fake result", bugfix.check(folder, truth, RUN), 0.0, 0.0)
    shutil.rmtree(folder / "pkg")
    (folder / "pkg").write_text("not a package")
    expect("bugfix pkg is a file", bugfix.check(folder, truth, RUN), 0.0, 0.0)
    expect("bugfix bad truth", bugfix.check(folder, {"modules": 5}, RUN), 0.0, 0.0)


def digests_only():
    """Print the first instance digests per (family, level); used for the cross-process check."""
    out = {}
    with tempfile.TemporaryDirectory() as root:
        for name, module in tasks.FAMILIES.items():
            for level in LEVELS:
                out[f"{name}/{level}"] = [digest(snapshot(generate(module, seed, level, root)[0]))
                                          for seed in range(5)]
    print(json.dumps(out))


def main():
    started = time.time()
    rows = []
    with tempfile.TemporaryDirectory(prefix="tasks-selftest-") as root:
        check_pools()
        for name in tasks.FAMILIES:
            for level in LEVELS:
                cell_root = pathlib.Path(tempfile.mkdtemp(dir=root))
                rows.append(run_cell(name, level, cell_root))
                shutil.rmtree(cell_root, ignore_errors=True)
        check_robustness(root)
    child = subprocess.run([sys.executable, str(HERE / "selftest.py"), "--digests"], capture_output=True,
                           text=True, env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "4242"})
    try:
        other = json.loads(child.stdout)
    except ValueError:
        other = {}
    for row in rows:
        if other.get(f"{row['family']}/{row['level']}") != row["digests"]:
            fail(f"{row['family']} L{row['level']}", "another process generates different bytes")

    print("family  level  sloppy mean  sloppy min..max  unfixed min..max  max bytes  rule sets  gen ms  check ms")
    for row in rows:
        s, u = row["sloppy"], row["unfixed"]
        unfixed = f"{min(u):.2f}..{max(u):.2f}" if u else "-"
        print(f"{row['family']:<7} {row['level']:>5}  {sum(s) / len(s):>11.3f}  {min(s):>7.2f}..{max(s):.2f}"
              f"  {unfixed:>16}  {row['bytes']:>9}  {row['rules']:>9}  {row['gen_ms']:>6.0f}  {row['check_ms']:>8.0f}")
    print(f"\n{len(tasks.FAMILIES)} families x {len(LEVELS)} levels x {len(SEEDS)} seeds,"
          f" visible={tasks.VISIBLE} heldout={tasks.HELDOUT}, {time.time() - started:.0f}s")
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} problem(s)")
        for line in FAILURES[:60]:
            print("  " + line)
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--digests"]:
        digests_only()
    else:
        sys.exit(main())
