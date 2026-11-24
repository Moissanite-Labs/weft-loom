"""spec: implement one function from scratch in solution.py from a written contract.

The function is drawn by seed from a pool (see _specpool_a / _specpool_b) and its
required behaviour depends on instance parameters stated in SPEC.md, in the prose and on
a machine-readable `- PARAMS: {...}` line. Level 1 changes one parameter away from the
usual behaviour, level 2 draws all of them, level 3 additionally replaces ValueError by a
sentinel return value.
"""

import inspect
import json
import pathlib

from . import _specpool_a, _specpool_b, _util

FAMILY = "spec"
POOL = {**_specpool_a.SPECS, **_specpool_b.SPECS}
SENTINELS = ["#ERR", "INVALID", "?!"]

TASK = """# Task: implement one function

Create `solution.py` in this directory (next to this file). It must define the function
`{signature}` exactly as specified in `SPEC.md`.

- The required behaviour depends on parameters that belong to this instance only
  (bounds, separators, tokens, switches). They are stated in `SPEC.md`, in the prose and
  on its `PARAMS` line. Do not assume the usual behaviour of similar functions: where the
  contract differs from what you expect, the contract wins.
- Read the rules for invalid input and for edge cases (empty input, boundaries) closely;
  the hidden tests cover them.
- Standard library only. `from solution import {func}` must work. The function must not
  print and must not read input.
- `SPEC.md` ends with worked examples. Run them against your code before you finish.

## Scoring

Hidden tests call the function with 12 to 16 different inputs. Score = fraction of calls
that give exactly the specified result.
"""

# Body of the hidden run script (appended to _util.RUNNER, after FUNC and CALLS lines).
# It is given the arguments only; the expected results stay in the referee.
TEST_BODY = r'''

results = []
ok, module = guarded(lambda: importlib.import_module("solution"), 2.0)
function = getattr(module, FUNC, None) if ok else None
for args in CALLS:
    if callable(function):
        results.append(attempt(lambda: function(*args), 0.5))
    else:
        results.append({"x": "no function"})
emit(results)
'''


def passes_outcome(outcome, case):
    """Whether one reported outcome meets one hidden case."""
    if case.get("raises"):
        return _util.raised_value_error(outcome)
    ok, value = _util.outcome_value(outcome)
    if not ok:
        return False
    try:
        return json.dumps(value, sort_keys=True) == json.dumps(case["value"], sort_keys=True)
    except Exception:
        return False


def _draw(spec, rng, level):
    """Instance parameters: the defaults with one change (level 1) or a full draw."""
    while True:
        drawn = spec["draw"](rng)
        changed = [key for key in drawn if drawn[key] != spec["defaults"][key]]
        if len(changed) >= 2:
            break
    if level == 1:
        key = rng.choice(changed)
        params = dict(spec["defaults"], **{key: drawn[key]})
    else:
        params = drawn
    params["on_error"] = "raise"
    if level >= 3:
        params["on_error"] = "return"
        params["error_value"] = rng.choice(SENTINELS)
        if "above_root" in params:
            params["above_root"] = "error"  # so that the error rule matters for path instances
    return params


def _outcome(spec, params, args):
    """Expected outcome of one call, computed with the reference implementation."""
    try:
        return {"args": args, "value": spec["impl"](params, *json.loads(json.dumps(args)))}
    except ValueError:
        if params["on_error"] == "return":
            return {"args": args, "value": params["error_value"]}
        return {"args": args, "raises": True}


def _show(func, case):
    """One worked-example line for SPEC.md."""
    call = f"{func}({', '.join(repr(arg) for arg in case['args'])})"
    if case.get("raises"):
        return f"    {call}  raises ValueError"
    return f"    {call} == {case['value']!r}"


def _spec_md(spec, params, examples):
    """SPEC.md text: parameters, contract, error rule and worked examples."""
    contract = spec["contract"](params)
    if "invalid" not in " ".join(contract):
        errors = ["No input is invalid for this instance: the function never needs to signal an error."]
    elif params["on_error"] == "raise":
        errors = ["For invalid input (every case called invalid above) raise `ValueError`."]
    else:
        errors = [
            "Extra rule of this instance: for invalid input (every case called invalid above) do NOT"
            f" raise. Return the string `{params['error_value']!r}` instead. No exception may leave"
            " the function for a str or int argument."]
    lines = [
        f"# SPEC: `{spec['func']}`", "",
        f"Implement `{spec['signature']}` in `solution.py`.", "",
        "## Instance parameters", "",
        "The contract below is already written for these values. They belong to this instance only;"
        " other instances of the same task use other values.", "",
        f"- Function: `{spec['func']}`",
        f"- PARAMS: {json.dumps(params)}", "",
        "## Contract", "", *contract, "",
        "## Errors", "", *errors, "",
        "## Worked examples", "",
        "Python notation; string arguments are shown as Python literals.", "",
        *[_show(spec["func"], case) for case in examples],
    ]
    return "\n".join(lines) + "\n"


def generate(seed, workdir, level=2):
    """Write one spec instance into workdir and return the hidden truth."""
    workdir, level = pathlib.Path(workdir), _util.clamp_level(level)
    rng = _util.make_rng(FAMILY, seed, level)
    name = rng.choice(sorted(POOL))
    spec = POOL[name]
    params = _draw(spec, rng, level)
    examples = [_outcome(spec, params, args) for args in spec["examples"](params, rng)]
    seen = {json.dumps(case["args"]) for case in examples}
    tests = []
    for args in spec["tests"](params, rng):
        if json.dumps(args) not in seen and len(tests) < 16:
            seen.add(json.dumps(args))
            tests.append(_outcome(spec, params, args))
    _util.write_text(workdir / "SPEC.md", _spec_md(spec, params, examples))
    _util.write_text(workdir / "TASK.md", TASK.format(signature=spec["signature"], func=spec["func"]))
    return {"family": FAMILY, "level": level, "spec": name, "func": spec["func"], "params": params,
            "tests": tests}


def check(workdir, truth, run_py):
    """Fraction of the hidden calls for which workdir/solution.py gives the expected outcome."""
    try:
        workdir = pathlib.Path(workdir)
        if not (workdir / "solution.py").is_file():
            return 0.0
        tests = truth["tests"]
        calls = [case["args"] for case in tests]
        body = f"FUNC = {truth['func']!r}\nCALLS = json.loads({json.dumps(calls)!r})\n" + TEST_BODY
        outcomes = _util.run_calls(run_py, body, workdir, len(tests), 10.0)
        if outcomes is None:
            return 0.0
        return sum(1 for outcome, case in zip(outcomes, tests) if passes_outcome(outcome, case)) / len(tests)
    except Exception:
        return 0.0


def _write_solution(workdir, use_defaults):
    """Write solution.py from the reference implementation, with the parameters read from
    SPEC.md or, for the sloppy variant, with the usual defaults."""
    workdir = pathlib.Path(workdir)
    text = (workdir / "SPEC.md").read_text(encoding="utf-8")
    func = _util.grab(text, "Function").strip("`")
    spec = next(entry for entry in POOL.values() if entry["func"] == func)
    params = json.loads(_util.grab(text, "PARAMS"))
    if use_defaults:
        params = dict(spec["defaults"], on_error="raise")
    impl = spec["impl"]
    source = "\n".join([
        '"""Solution built from the reference implementation."""', "", "import json", "",
        f"PARAMS = json.loads({json.dumps(params)!r})", "", "",
        inspect.getsource(impl).rstrip("\n"), "", "",
        f"def {func}(*args):",
        "    try:",
        f"        return {impl.__name__}(PARAMS, *args)",
        "    except ValueError:",
        '        if PARAMS["on_error"] == "return":',
        '            return PARAMS["error_value"]',
        "        raise", "",
    ])
    _util.write_text(workdir / "solution.py", source)


def solve_from_files(workdir):
    """Reference solver: reads the function name and PARAMS from SPEC.md, writes solution.py."""
    _write_solution(workdir, use_defaults=False)


def sloppy_solve(workdir):
    """Careless solver: implements the usual behaviour and ignores the instance parameters."""
    _write_solution(workdir, use_defaults=True)
