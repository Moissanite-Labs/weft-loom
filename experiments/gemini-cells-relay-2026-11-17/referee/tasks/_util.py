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

# Prefix of every hidden test script. It gives the family-specific body two helpers:
# guarded(fn, limit) runs fn() under a time limit and never raises; finish(passed, total)
# prints the single JSON result line and exits. The whole script stays under BUDGET
# seconds even if every call hangs.
HARNESS = r'''
import contextlib, importlib, io, json, os, signal, sys, time

sys.dont_write_bytecode = True
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
_OUT = sys.stdout
_DEADLINE = time.monotonic() + __BUDGET__


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
    """Return (True, fn()) or (False, None) on any exception, exit or timeout."""
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


def finish(passed, total):
    _OUT.write("\n" + json.dumps({"passed": passed, "total": total, "nonce": "__NONCE__"}) + "\n")
    _OUT.flush()
    os._exit(0)

'''


def last_json_line(stdout):
    """Parse the last non-empty stdout line as JSON; None when that is not possible."""
    try:
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        lines = [line for line in str(stdout).splitlines() if line.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception:
        return None


def run_hidden(run_py, body, cwd, total, timeout_s=10.0):
    """Run HARNESS + body through run_py and return passed / total (0.0 on any trouble).

    The result line must carry a nonce drawn here, so output printed by the code under
    test cannot be mistaken for the result.
    """
    try:
        nonce = secrets.token_hex(8)
        script = HARNESS.replace("__NONCE__", nonce).replace("__BUDGET__", "6.0") + body
        _, stdout = run_py(script, pathlib.Path(cwd), timeout_s)
        record = last_json_line(stdout)
        if not isinstance(record, dict) or record.get("nonce") != nonce:
            return 0.0
        passed = record.get("passed")
        if type(passed) is not int or record.get("total") != total or total <= 0:
            return 0.0
        return max(0.0, min(1.0, passed / total))
    except Exception:
        return 0.0
