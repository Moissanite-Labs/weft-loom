"""bugfix: a small package whose modules each carry one planted bug.

The modules are drawn by seed from a pool of function specs (see _bugpool_a / _bugpool_b)
and each gets one of that spec's bug mutations. SPEC.md states every contract with worked
examples. Level 1 adds, per module, one call that is currently wrong; level 2 shows the
standard examples (some pass on the buggy code, some may not); level 3 has four modules
instead of three and shows only examples that already pass.
"""

import json
import pathlib

from . import _bugpool_a, _bugpool_b, _util

FAMILY = "bugfix"
POOL = {**_bugpool_a.SPECS, **_bugpool_b.SPECS}

TASK = """# Task: fix the bugs

`pkg/` is a small Python package with {count} modules: {names}.
Each module has exactly ONE bug. `SPEC.md` states the contract of every function, with
worked examples.

Fix the modules so that every function meets `SPEC.md`.

- Edit the files in place (`pkg/<module>.py`). Do not rename modules, functions, classes
  or parameters, and keep every module importable.
- Standard library only. No printing, no input.
- The examples in `SPEC.md` are not a complete test: most of them already pass on the
  buggy code. Compare the code with the contract, in particular at boundaries and edge
  cases (empty input, equal values, last element, several digits, repeated items).

## Scoring

Hidden tests import each module and run about a dozen assertions per module, most of them
on edge cases named in the contract. Score = fraction of all assertions that pass. A
module that fails to import, or hangs, fails all of its assertions.
"""

# Body of the hidden test script (appended to _util.HARNESS, after a MODULES = ... line).
TEST_BODY = r'''

def _holds(namespace, expression, expected):
    if expected == "ValueError":
        try:
            eval(expression, namespace)
        except ValueError:
            return True
        return False
    return eval(expression, namespace) == eval(expected, {})


passed = total = 0
for entry in MODULES:
    total += len(entry["tests"])
    ok, module = guarded(lambda: importlib.import_module("pkg." + entry["module"]), 2.0)
    if not ok:
        continue
    namespace = dict(vars(module))
    for expression, expected in entry["tests"]:
        ok, value = guarded(lambda: _holds(namespace, expression, expected), 0.5)
        if ok and value is True:
            passed += 1
finish(passed, total)
'''


def buggy_source(name, bug):
    """Module text of pool spec `name` with bug number `bug` planted."""
    old, new = POOL[name]["bugs"][bug]
    source = POOL[name]["source"]
    if source.count(old) != 1:
        raise ValueError(f"bug {bug} of {name} does not apply exactly once")
    return source.replace(old, new)


def holds(source, pairs):
    """For each (expression, expected) pair, whether it holds for the given pool source.
    Runs pool code in-process; never used on files from a workdir."""
    namespace = {}
    exec(source, namespace)
    results = []
    for expression, expected in pairs:
        try:
            if expected == "ValueError":
                try:
                    eval(expression, namespace)
                    results.append(False)
                except ValueError:
                    results.append(True)
            else:
                results.append(eval(expression, namespace) == eval(expected, {}))
        except Exception:
            results.append(False)
    return results


def _select_tests(name, bug):
    """Hidden assertions for one planted bug: every pool test the bug breaks plus as many
    that it does not break (at least 8 in total where the pool allows), in pool order."""
    tests = POOL[name]["tests"]
    verdicts = holds(buggy_source(name, bug), tests)
    broken = [index for index, ok in enumerate(verdicts) if not ok]
    intact = [index for index, ok in enumerate(verdicts) if ok]
    extra = intact[:max(len(broken), 8 - len(broken))]
    return [list(tests[index]) for index in sorted(broken + extra)]


def _show(expression, expected):
    """One example line for SPEC.md."""
    if expected == "ValueError":
        return f"    {expression}  raises ValueError"
    return f"    {expression} == {expected}"


def _spec_md(chosen, level, rng):
    """SPEC.md text for the chosen modules. Two or all three of a module's examples are
    shown; every pair contains at least one example that passes on the buggy code."""
    lines = ["# SPEC", "",
             "Contracts of the functions in `pkg/`. A fixed module must satisfy its whole contract, not"
             " only the examples."]
    if level >= 3:
        lines.append("Note: every example below already passes on the code as given; the bugs are in"
                     " cases the examples do not cover.")
    for item in chosen:
        spec = POOL[item["spec"]]
        source = buggy_source(item["spec"], item["bug"])
        examples = spec["examples"]
        if level >= 3:
            examples = [pair for pair, ok in zip(examples, holds(source, examples)) if ok]
        else:
            examples = [examples[index] for index in rng.choice([[0, 1, 2], [0, 1], [0, 2], [1, 2]])]
        lines += ["", f"## `pkg/{item['spec']}.py`", "", spec["contract"], "", "Examples:", ""]
        lines += [_show(*pair) for pair in examples]
        if level == 1:
            failing = [pair for pair, ok in zip(spec["tests"], holds(source, spec["tests"])) if not ok]
            lines += ["", "Currently wrong (this call does not behave like this yet):", "", _show(*failing[0])]
    return "\n".join(lines) + "\n"


def generate(seed, workdir, level=2):
    """Write one bugfix instance into workdir and return the hidden truth."""
    workdir, level = pathlib.Path(workdir), _util.clamp_level(level)
    rng = _util.make_rng(FAMILY, seed, level)
    names = rng.sample(sorted(POOL), 4 if level >= 3 else 3)
    chosen = []
    for name in names:
        bug = rng.randrange(len(POOL[name]["bugs"]))
        chosen.append({"spec": name, "bug": bug, "tests": _select_tests(name, bug)})
    _util.write_text(workdir / "pkg" / "__init__.py", '"""Small utility functions; see SPEC.md."""\n')
    for item in chosen:
        _util.write_text(workdir / "pkg" / f"{item['spec']}.py", buggy_source(item["spec"], item["bug"]))
    _util.write_text(workdir / "SPEC.md", _spec_md(chosen, level, rng))
    listing = ", ".join(f"`pkg/{name}.py`" for name in names)
    _util.write_text(workdir / "TASK.md", TASK.format(count=len(names), names=listing))
    return {"family": FAMILY, "level": level, "modules": chosen}


def check(workdir, truth, run_py):
    """Fraction of the hidden assertions that pass on the modules now in workdir/pkg."""
    try:
        workdir = pathlib.Path(workdir)
        if not (workdir / "pkg").is_dir():
            return 0.0
        modules = [{"module": item["spec"], "tests": item["tests"]} for item in truth["modules"]]
        total = sum(len(entry["tests"]) for entry in modules)
        body = f"MODULES = json.loads({json.dumps(modules)!r})\n" + TEST_BODY
        return _util.run_hidden(run_py, body, workdir, total, 10.0)
    except Exception:
        return 0.0


def _fix(workdir, limit):
    """Overwrite up to `limit` pool modules found in workdir/pkg with their correct text."""
    found = sorted(path for path in (pathlib.Path(workdir) / "pkg").glob("*.py") if path.stem in POOL)
    for path in found[:limit]:
        _util.write_text(path, POOL[path.stem]["source"])


def solve_from_files(workdir):
    """Reference solver: recognises the modules by file name and writes the fixed source."""
    _fix(workdir, limit=99)


def sloppy_solve(workdir):
    """Careless solver: fixes only the first module and leaves the other bugs in."""
    _fix(workdir, limit=1)
