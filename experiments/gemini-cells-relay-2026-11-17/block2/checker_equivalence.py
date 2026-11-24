#!/usr/bin/env python3
"""The pilot's hidden checker against block 2's, on honest solutions and on forgeries.

Up to the pilot, the code families scored a cell's code in a process that also held the
expected results and the function that reported the score. Block 2's checker sends only the
inputs into that process and compares the reported values in the referee. This script
shows two things on generated instances:

  1. On honest solutions, including ones that return subclasses of plain types or the
     wrong type, both checkers give the same score on every instance.
  2. Code that calls the old reporting function, or that returns an object equal to
     everything, scored high on the old checker. On the new one it scores no more than a
     named honest variant on each instance. Code that calls the new reporting function
     with made-up outcomes scores no more than code that honestly raises ValueError on
     every call: it can claim only what it could have returned.

The old checker is read from git at the pilot's commit. Run from the record folder:

    python3 -I -B block2/checker_equivalence.py [--seeds N]

Exit 0 when every claim above holds. Needs git and python3; no model, no sandbox.
"""

import importlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
REL = "experiments/gemini-cells-relay-2026-11-17/referee/tasks"
PILOT_COMMIT = "6726330"  # the record as pushed with the pilot's results
SEEDS = range(int(sys.argv[2]) if sys.argv[1:2] == ["--seeds"] else 20)
LEVELS = (1, 2, 3)

sys.dont_write_bytecode = True


def load_old(holder):
    """Import the pilot's task package from git as `oldtasks`."""
    target = holder / "oldtasks"
    target.mkdir()
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE, check=True,
                          capture_output=True, text=True).stdout.strip()
    names = subprocess.run(["git", "ls-tree", "--name-only", f"{PILOT_COMMIT}:{REL}"], cwd=root,
                           check=True, capture_output=True, text=True).stdout.split()
    for name in names:
        if name.endswith(".py"):
            blob = subprocess.run(["git", "show", f"{PILOT_COMMIT}:{REL}/{name}"], cwd=root,
                                  check=True, capture_output=True).stdout
            (target / name).write_bytes(blob)
    if not (target / "__init__.py").is_file():
        raise SystemExit(f"could not read the pilot's task package at {PILOT_COMMIT}")
    sys.path.insert(0, str(holder))
    return importlib.import_module("oldtasks")


sys.path.insert(0, str(HERE))
from referee import tasks as new  # noqa: E402

RUN = new.local_run_py

# ----------------------------------------------------------------------- variants

WRAP_TYPES = '''

import collections as _c, enum as _e, functools as _ft, types as _ty
class _L(list): pass
class _S(str): pass
class _I(int): pass
def _sub(value):
    if isinstance(value, bool): return value
    if isinstance(value, dict): return _c.OrderedDict(value)
    if isinstance(value, list): return _L(value)
    if isinstance(value, str): return _S(value)
    if isinstance(value, int): return _I(value)
    return value
for _n, _f in list(globals().items()):
    if isinstance(_f, _ty.FunctionType) and not _n.startswith("_"):
        globals()[_n] = (lambda f: _ft.wraps(f)(lambda *a, **k: _sub(f(*a, **k))))(_f)
'''

WRAP_TUPLE = '''

import functools as _ft, types as _ty
for _n, _f in list(globals().items()):
    if isinstance(_f, _ty.FunctionType) and not _n.startswith("_"):
        globals()[_n] = (lambda f: _ft.wraps(f)(
            lambda *a, **k: (lambda r: tuple(r) if isinstance(r, list) else r)(f(*a, **k))))(_f)
'''

WRAP_FLOAT = '''

import functools as _ft, types as _ty
for _n, _f in list(globals().items()):
    if isinstance(_f, _ty.FunctionType) and not _n.startswith("_"):
        globals()[_n] = (lambda f: _ft.wraps(f)(
            lambda *a, **k: (lambda r: float(r) if type(r) is int else r)(f(*a, **k))))(_f)
'''

ALWAYS_EQUAL = '''

import types as _ty
class _AE:
    def __eq__(self, other):
        return True
    __hash__ = None
for _n, _f in list(globals().items()):
    if isinstance(_f, _ty.FunctionType) and not _n.startswith("_"):
        globals()[_n] = (lambda f: lambda *a, **k: _AE())(_f)
'''

ALWAYS_RAISE = '''

import types as _ty
def _raise(*a, **k):
    raise ValueError("always")
for _n, _f in list(globals().items()):
    if isinstance(_f, _ty.FunctionType) and not _n.startswith("_"):
        globals()[_n] = _raise
'''

CALL_OLD_FINISH = '''
import __main__ as _m
_t = sum(len(e.get("tests", [])) for e in getattr(_m, "MODULES", [])) or len(getattr(_m, "TESTS", []))
if hasattr(_m, "finish") and _t:
    _m.finish(_t, _t)
'''

CALL_NEW_EMIT = '''
import __main__ as _m
_n = sum(len(e.get("exprs", [])) for e in getattr(_m, "MODULES", [])) or len(getattr(_m, "CALLS", []))
if hasattr(_m, "emit") and _n:
    _m.emit([{"x": "ValueError"}] * _n)
'''


def pkg_files(folder):
    return sorted((folder / "pkg").glob("*.py"))


def edit_bugfix(folder, family, variant):
    """Turn a fresh bugfix instance into one variant. Returns False if not applicable."""
    files = [path for path in pkg_files(folder) if path.name != "__init__.py"]
    if variant == "as shipped":
        return True
    if variant == "all fixed":
        family.solve_from_files(folder)
        return True
    if variant == "first fixed":
        family.sloppy_solve(folder)
        return True
    if variant.startswith("fixed, "):
        family.solve_from_files(folder)
        tail = {"fixed, subclass results": WRAP_TYPES, "fixed, tuples for lists": WRAP_TUPLE,
                "fixed, floats for ints": WRAP_FLOAT}[variant]
        for path in files:
            path.write_text(path.read_text() + tail)
        return True
    if variant == "always raises ValueError":
        for path in files:
            path.write_text(path.read_text() + ALWAYS_RAISE)
        return True
    if variant == "forgery: always-equal results":
        for path in files:
            path.write_text(path.read_text() + ALWAYS_EQUAL)
        return True
    if variant == "forgery: calls old finish()":
        files[0].write_text(CALL_OLD_FINISH)
        return True
    if variant == "forgery: calls new emit()":
        files[0].write_text(CALL_NEW_EMIT)
        return True
    raise KeyError(variant)


def edit_spec(folder, family, variant):
    solution = folder / "solution.py"
    if variant == "no solution":
        return True
    if variant == "reference":
        family.solve_from_files(folder)
        return True
    if variant == "sloppy":
        family.sloppy_solve(folder)
        return True
    if variant.startswith("reference, "):
        family.solve_from_files(folder)
        tail = {"reference, subclass results": WRAP_TYPES, "reference, tuples for lists": WRAP_TUPLE,
                "reference, floats for ints": WRAP_FLOAT}[variant]
        solution.write_text(solution.read_text() + tail)
        return True
    if variant == "always raises ValueError":
        family.sloppy_solve(folder)
        solution.write_text(solution.read_text() + ALWAYS_RAISE)
        return True
    if variant == "forgery: always-equal results":
        family.sloppy_solve(folder)
        solution.write_text(solution.read_text() + ALWAYS_EQUAL)
        return True
    if variant == "forgery: calls old finish()":
        solution.write_text(CALL_OLD_FINISH)
        return True
    if variant == "forgery: calls new emit()":
        solution.write_text(CALL_NEW_EMIT)
        return True
    raise KeyError(variant)


PLAN = {
    "bugfix": (edit_bugfix, ["as shipped", "all fixed", "first fixed", "fixed, subclass results",
                             "fixed, tuples for lists", "fixed, floats for ints", "always raises ValueError",
                             "forgery: always-equal results", "forgery: calls old finish()",
                             "forgery: calls new emit()"],
               {"forgery: always-equal results": "as shipped", "forgery: calls old finish()": "as shipped",
                "forgery: calls new emit()": "always raises ValueError"}),
    "spec": (edit_spec, ["no solution", "reference", "sloppy", "reference, subclass results",
                         "reference, tuples for lists", "reference, floats for ints",
                         "always raises ValueError", "forgery: always-equal results", "forgery: calls old finish()",
                         "forgery: calls new emit()"],
             {"forgery: always-equal results": "sloppy", "forgery: calls old finish()": "no solution",
              "forgery: calls new emit()": "always raises ValueError"}),
}


def main():
    holder = pathlib.Path(tempfile.mkdtemp(prefix="checker-eq-"))
    failures = []
    rows = []
    try:
        old = load_old(holder)
        for name, (edit, variants, floors) in PLAN.items():
            old_family, new_family = old.FAMILIES[name], new.FAMILIES[name]
            scores = {variant: [] for variant in variants}
            for level in LEVELS:
                for seed in SEEDS:
                    for variant in variants:
                        folder = pathlib.Path(tempfile.mkdtemp(dir=holder))
                        truth = new_family.generate(seed, folder, level)
                        if truth != old_family.generate(seed, pathlib.Path(tempfile.mkdtemp(dir=holder)), level):
                            failures.append(f"{name} seed {seed} level {level}: generators differ")
                        edit(folder, new_family, variant)
                        scores[variant].append((old_family.check(folder, truth, RUN),
                                                new_family.check(folder, truth, RUN)))
                        shutil.rmtree(folder, ignore_errors=True)
            for variant in variants:
                pairs = scores[variant]
                same = sum(1 for o, n in pairs if o == n)
                mean_old = sum(o for o, _ in pairs) / len(pairs)
                mean_new = sum(n for _, n in pairs) / len(pairs)
                rows.append((name, variant, len(pairs), same, mean_old, mean_new))
                if variant.startswith("forgery"):
                    floor = floors[variant]
                    above = sum(1 for (_, n), (_, f) in zip(pairs, scores[floor]) if n > f)
                    rows[-1] += (floor, above)
                    if above:
                        failures.append(f"{name} {variant}: new score above {floor!r} on {above} instances")
                elif same != len(pairs):
                    failures.append(f"{name} {variant}: old and new differ on {len(pairs) - same} instances")
    finally:
        shutil.rmtree(holder, ignore_errors=True)
    print(f"Old checker: commit {PILOT_COMMIT}. Seeds {SEEDS.start}..{SEEDS.stop - 1}, levels 1..3.\n")
    print(f"{'family':7} {'variant':33} {'n':>4} {'same':>5} {'old mean':>9} {'new mean':>9}  forgery check")
    for row in rows:
        name, variant, n, same, mean_old, mean_new = row[:6]
        extra = f"  new above {row[6]!r} on {row[7]} of {n}" if len(row) > 6 else ""
        print(f"{name:7} {variant:33} {n:4d} {same:5d} {mean_old:9.3f} {mean_new:9.3f}{extra}")
    print()
    if failures:
        print("FAILURES:")
        for line in failures:
            print("  " + line)
        return 1
    print("Honest variants: identical scores on every instance. Forgeries: on every instance the new"
          " checker gives no more than the honest variant named beside it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
