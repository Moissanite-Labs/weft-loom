"""Small helpers shared by the task families (standard library only)."""

import json
import math
import pathlib
import random
import secrets
from datetime import datetime, timezone

MAX_ANSWER_BYTES = 1_000_000
EPOCH_2026 = 1767225600  # 2026-01-01T00:00:00Z

# Timestamp patterns used by the data families ("epoch" = integer seconds since 1970, UTC).
TS_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%Y%m%d-%H%M%S",
    "%H:%M:%S %d-%m-%Y",
    "epoch",
]


def make_rng(family, seed, level, salt=""):
    """Deterministic random generator for (family, seed, level, salt)."""
    return random.Random(f"{family}/{int(seed)}/{int(level)}/{salt}")


def clamp_level(level):
    """Difficulty level as an int in 1..3 (anything else falls back to the nearest level)."""
    try:
        return max(1, min(3, int(level)))
    except (TypeError, ValueError):
        return 2


def write_text(path, text):
    """Write UTF-8 text with LF line ends, creating parent folders."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def fmt_ts(epoch, pattern):
    """Format epoch seconds (UTC) with one of TS_FORMATS."""
    if pattern == "epoch":
        return str(epoch)
    return datetime.fromtimestamp(epoch, timezone.utc).strftime(pattern)


def parse_ts(text, pattern):
    """Inverse of fmt_ts: text to epoch seconds (UTC)."""
    if pattern == "epoch":
        return int(text)
    return int(datetime.strptime(text, pattern).replace(tzinfo=timezone.utc).timestamp())


def iso(epoch):
    """ISO 8601 UTC text for epoch seconds."""
    return fmt_ts(epoch, "%Y-%m-%dT%H:%M:%SZ")


def grab(text, label):
    """Value of the line '- <label>: <value>' in a FORMAT.md / SPEC.md text."""
    prefix = f"- {label}: "
    for line in text.split("\n"):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    raise KeyError(label)


def load_json_file(path):
    """Parse a JSON file defensively: None when missing, not a file, too big or malformed."""
    try:
        path = pathlib.Path(path)
        if not path.is_file() or path.stat().st_size > MAX_ANSWER_BYTES:
            return None
        return json.loads(path.read_bytes().decode("utf-8-sig"))
    except Exception:
        return None


def real_number(value):
    """True for a finite int or float (bool excluded)."""
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except Exception:
        return False


def whole_number(value):
    """The int behind an int or an integral float; None for anything else."""
    if not real_number(value) or value != int(value):
        return None
    return int(value)


def shares_pair(first, second):
    """True when two answer dicts have an identical (key, value) pair."""
    return any(key in second and second[key] == value for key, value in first.items())


def score_fields(answer, expected, fields):
    """Mean over expected keys of the fraction of integer `fields` that match exactly."""
    if not isinstance(answer, dict) or not expected:
        return 0.0
    points = 0
    for key, want in expected.items():
        got = answer.get(key)
        if isinstance(got, dict):
            points += sum(1 for field in fields if whole_number(got.get(field)) == want[field])
    return points / (len(fields) * len(expected))


# --------------------------------------------------------------- hidden test harness
#
# The code families (bugfix, spec) must run the cell's code to score it. Up to the pilot
# of 2026-11-17 the expected results, the comparison and the line that reported the score
# all lived in the same Python process as the cell's code, so code written by a cell could
# have called the reporting function itself and claimed full marks. From block 2 on, the
# process that runs cell code is given only the inputs. It reports what each call returned,
# encoded as plain data, and the referee compares that with the expected results in its own
# process. Code in the sandbox can then decide what it reports, which is no more than it
# could do by returning those values: it never sees an expected result.

# Prefix of every hidden run script. It gives the family-specific body two helpers:
# attempt(fn, limit) runs fn() under a time limit and returns the encoded outcome, and
# emit(results) prints the single JSON result line and exits. The whole script stays
# under BUDGET seconds even if every call hangs.
RUNNER = r"""
import contextlib, importlib, io, json, os, signal, sys, time

sys.dont_write_bytecode = True
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
_OUT = sys.stdout
_DEADLINE = time.monotonic() + __BUDGET__
_MAX_VALUE_CHARS = __MAX_VALUE_CHARS__


class _Timeout(BaseException):
    pass


def _on_alarm(signum, frame):
    raise _Timeout()


try:
    signal.signal(signal.SIGALRM, _on_alarm)
    _TIMER = True
except Exception:
    _TIMER = False


def guarded(fn, limit):
    # Return (True, fn()) or (False, None) on any exception, exit or timeout.
    remaining = _DEADLINE - time.monotonic()
    if remaining <= 0:
        return False, None
    try:
        if _TIMER:
            signal.setitimer(signal.ITIMER_REAL, max(0.01, min(limit, remaining)))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return True, fn()
        finally:
            if _TIMER:
                signal.setitimer(signal.ITIMER_REAL, 0)
    except BaseException:
        return False, None


def _enc(value, depth=0):
    # Plain-data encoding of a returned value. Subclasses are read through the base type.
    if depth > 60:
        raise ValueError("too deep")
    if value is None:
        return None
    if isinstance(value, bool):
        return {"b": bool(value)}
    if isinstance(value, int):
        return {"i": int.__repr__(value)}
    if isinstance(value, float):
        return {"f": float.__repr__(value)}
    if isinstance(value, str):
        return {"s": str.__str__(value)}
    if isinstance(value, list):
        return {"l": [_enc(item, depth + 1) for item in list.__iter__(value)]}
    if isinstance(value, tuple):
        return {"t": [_enc(item, depth + 1) for item in tuple.__iter__(value)]}
    if isinstance(value, dict):
        return {"d": [[_enc(k, depth + 1), _enc(v, depth + 1)] for k, v in dict.items(value)]}
    if isinstance(value, frozenset):
        return {"F": [_enc(item, depth + 1) for item in frozenset.__iter__(value)]}
    if isinstance(value, set):
        return {"S": [_enc(item, depth + 1) for item in set.__iter__(value)]}
    raise TypeError("not plain data")


def attempt(fn, limit):
    # {"v": encoded value}, {"x": "ValueError"} when fn raised ValueError, else {"x": reason}.
    def inner():
        try:
            value = fn()
        except ValueError:
            return {"x": "ValueError"}
        try:
            encoded = _enc(value)
            if len(json.dumps(encoded)) > _MAX_VALUE_CHARS:
                return {"x": "too big"}
            return {"v": encoded}
        except Exception:
            return {"x": "not plain data"}
    ok, outcome = guarded(inner, limit)
    return outcome if ok and isinstance(outcome, dict) else {"x": "failed"}


def emit(results):
    _OUT.write("\n" + json.dumps({"results": results, "nonce": "__NONCE__"}) + "\n")
    _OUT.flush()
    os._exit(0)

"""

MAX_VALUE_CHARS = 100_000
MAX_DEPTH = 60


def last_json_line(stdout):
    """Parse the last non-empty stdout line as JSON; None when that is not possible."""
    try:
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        lines = [line for line in str(stdout).splitlines() if line.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None


def run_calls(run_py, body, cwd, count, timeout_s=10.0):
    """Run RUNNER + body through run_py; the list of `count` outcomes, or None on any trouble.

    The result line must carry a nonce drawn here, so stray output from the code under test
    is not read as the result. The body sees no expected result.
    """
    try:
        nonce = secrets.token_hex(8)
        script = (RUNNER.replace("__NONCE__", nonce).replace("__BUDGET__", "6.0")
                  .replace("__MAX_VALUE_CHARS__", str(MAX_VALUE_CHARS)) + body)
        _, stdout = run_py(script, pathlib.Path(cwd), timeout_s)
        record = last_json_line(stdout)
        if not isinstance(record, dict) or record.get("nonce") != nonce:
            return None
        results = record.get("results")
        if type(results) is not list or len(results) != count or count <= 0:
            return None
        return [item if type(item) is dict else {"x": "malformed"} for item in results]
    except Exception:
        return None


def decode(encoded, depth=0):
    """Python value of an outcome's "v" field. Raises ValueError on anything malformed.
    Runs in the referee on untrusted data, so it builds plain values only."""
    if depth > MAX_DEPTH:
        raise ValueError("too deep")
    if encoded is None:
        return None
    if type(encoded) is not dict or len(encoded) != 1:
        raise ValueError("malformed")
    (tag, body), = encoded.items()
    if tag == "b" and type(body) is bool:
        return body
    if tag == "i" and type(body) is str and 0 < len(body) <= 4300 and body.lstrip("-").isdigit() \
            and body.isascii():
        return int(body)
    if tag == "f" and type(body) is str and len(body) <= 40 and body.isascii():
        return float(body)
    if tag == "s" and type(body) is str:
        return body
    if tag in ("l", "t", "S", "F") and type(body) is list:
        items = [decode(item, depth + 1) for item in body]
        return {"l": list, "t": tuple, "S": set, "F": frozenset}[tag](items)
    if tag == "d" and type(body) is list:
        out = {}
        for pair in body:
            if type(pair) is not list or len(pair) != 2:
                raise ValueError("malformed pair")
            out[decode(pair[0], depth + 1)] = decode(pair[1], depth + 1)
        return out
    raise ValueError("malformed")


def outcome_value(outcome):
    """(True, value) for an outcome that returned plain data, else (False, None)."""
    try:
        if type(outcome) is dict and set(outcome) == {"v"}:
            return True, decode(outcome["v"])
    except Exception:
        pass
    return False, None


def raised_value_error(outcome):
    """True when the outcome says the call raised ValueError."""
    return type(outcome) is dict and outcome == {"x": "ValueError"}
