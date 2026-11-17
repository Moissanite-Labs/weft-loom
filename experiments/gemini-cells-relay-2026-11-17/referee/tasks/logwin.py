"""logwin: per-service error counts and longest error gap outside maintenance windows.

Quirks drawn per instance: field separator and order, timestamp pattern, level names,
comment prefix, multi-line continuation records, window list with an inclusive or
exclusive end and optional per-service scope. Level 1 has one log file and global windows
only; level 2 spreads the records over several files; level 3 adds a clock correction for
one of the files.
"""

import json
import pathlib
import re

from . import _util

FAMILY = "logwin"
SEPARATORS = [" | ", "\t", " ; ", " :: "]
LEVEL_NAMES = [
    ["D", "I", "W", "E"], ["DBG", "INF", "WRN", "ERR"], ["debug", "info", "warning", "error"],
    ["10", "20", "30", "40"], ["fine", "note", "alert", "fault"],
]
CANON = ["DEBUG", "INFO", "WARN", "ERROR"]
SERVICES = ["auth", "billing", "search", "gateway", "mailer", "cache", "ingest", "reports",
            "scheduler", "storage"]
COMMENTS = ["#", ";", "//", "--", "%"]
NODES = ["node-a.log", "node-b.log", "node-c.log"]
PHRASES = ["request done", "cache refresh", "queue depth", "retry scheduled", "conn reset",
           "slow query", "heartbeat ok", "token expired", "disk usage", "job finished"]
TRACES = ["at worker.run (line 88)", "caused by: timeout", "retrying in 5s", "stack: handler > pool",
          "payload truncated"]

TASK = """# Task: errors outside maintenance windows

`data/` holds service logs. For every service report

- `errors`: the number of ERROR-level records that are NOT inside a maintenance window,
- `max_gap_s`: the longest gap, in whole seconds, between two consecutive counted errors
  of that service (0 if it has fewer than two counted errors).

The line format, the field order, the timestamp pattern, the level names, the comment
prefix, the maintenance windows and their boundary rule are specific to this instance.
All of it is stated in `FORMAT.md`. Read it before writing any code: records can span
several lines, and words like "error" inside a message do not make a record an error.

## Output

Write `answer.json` in this directory (next to this file): one JSON object with one entry
per service, integers only. Shape:

    {"service-a": {"errors": 12, "max_gap_s": 5400}, "service-b": {"errors": 0, "max_gap_s": 0}}

## Check your work

`example/` is a tiny dataset with the same layout and exactly the same rules and windows
(`example/data/...`). Its correct answer is in `example/expected.json`. Run your solver
on `example/` first and compare, then run it on `data/`.

## Scoring

Per service: half a point for the right `errors`, half for the right `max_gap_s`. The
score is the mean over all services.
"""


def _draw_params(rng, level):
    """Draw the rule parameters of one instance."""
    services = rng.sample(SERVICES, rng.randint(4, 5) if level == 1 else rng.randint(4, 7))
    affected = sorted(rng.sample(services, max(1, len(services) // 2)))
    t0 = _util.EPOCH_2026 + rng.randrange(300) * 86400 + rng.randrange(24) * 3600
    span = rng.choice([18, 24, 36, 48]) * 3600
    n_windows = rng.randint(2, 3) if level == 1 else rng.randint(3, 5)
    slot = span // n_windows
    windows = []
    for index in range(n_windows):
        length = rng.randrange(10, 41) * 60
        start = t0 + index * slot + rng.randrange((slot - length) // 60) * 60
        scoped = level > 1 and index != 1 and (index == 0 or rng.random() < 0.6)
        windows.append({"start": start, "end": start + length,
                        "service": rng.choice(affected) if scoped else None})
    files = NODES[:1] if level == 1 else NODES[:3 if level >= 3 else rng.randint(2, 3)]
    order = ["timestamp", "level", "service"]
    rng.shuffle(order)
    correction = {}
    if level >= 3:
        correction = {rng.choice(files[1:]): rng.choice([-1, 1]) * rng.randrange(20, 95)}
    return {
        "services": services, "affected": affected, "t0": t0, "span": span, "windows": windows,
        "end_inclusive": rng.random() < 0.5, "files": files, "order": order + ["message"],
        "sep": rng.choice(SEPARATORS), "ts": rng.choice(_util.TS_FORMATS),
        "levels": rng.choice(LEVEL_NAMES), "comment": rng.choice(COMMENTS), "correction": correction,
    }


def _inside(when, service, P):
    """True when a record of `service` at time `when` falls inside a window that applies to it."""
    for window in P["windows"]:
        if window["service"] in (None, service):
            if window["start"] <= when < window["end"] or (P["end_inclusive"] and when == window["end"]):
                return True
    return False


def _records(rng, P, services, count, quiet=None):
    """Logical records {t, svc, lvl, file}. Services outside P['affected'] never have an
    error inside a window; affected ones get errors planted on the window boundaries. The
    `quiet` service keeps at most one error (the "fewer than two" case)."""
    records = []
    spare = rng.randrange(2)
    for _ in range(count):
        record = {"t": P["t0"] + rng.randrange(P["span"]), "svc": rng.choice(services),
                  "lvl": rng.choices(range(4), weights=[15, 45, 20, 20])[0]}
        if record["lvl"] == 3 and record["svc"] not in P["affected"]:
            if _inside(record["t"], record["svc"], P):
                record["lvl"] = 2
            elif record["svc"] == quiet:
                spare -= 1
                record["lvl"] = 3 if spare >= 0 else 1
        records.append(record)
    for window in P["windows"]:
        targets = [window["service"]] if window["service"] else P["affected"]
        for service in targets:
            if service in services:
                for when in (window["start"], window["end"], rng.randrange(window["start"] + 1, window["end"])):
                    records.append({"t": when, "svc": service, "lvl": 3})
    for record in records:
        record["file"] = rng.choice(P["files"])
    return records


def _truth(records, P):
    """Counted errors and longest gap per service (the hidden truth)."""
    answer = {}
    for service in sorted({record["svc"] for record in records}):
        times = sorted(r["t"] for r in records
                       if r["svc"] == service and r["lvl"] == 3 and not _inside(r["t"], service, P))
        gaps = [later - earlier for earlier, later in zip(times, times[1:])]
        answer[service] = {"errors": len(times), "max_gap_s": max(gaps, default=0)}
    return answer


def _line(record, message, P):
    """Render one record line; timestamps of a corrected file are written uncorrected."""
    raw = record["t"] - P["correction"].get(record["file"], 0)
    cells = {"timestamp": _util.fmt_ts(raw, P["ts"]), "level": P["levels"][record["lvl"]],
             "service": record["svc"], "message": message}
    return P["sep"].join(cells[name] for name in P["order"])


def _message(rng, P):
    """A message; some contain level names or the separator to trip naive parsers."""
    error = P["levels"][3]
    if rng.random() < 0.12:
        return rng.choice(["no ERROR here", f"last level {error}", "ERROR budget ok",
                           f"upstream{P['sep']}{error}{P['sep']}ignored"])
    return f"{rng.choice(PHRASES)} {rng.randrange(100, 999)}"


def _write_logs(root, rng, records, P, traps):
    """Write the log files of one dataset under root/data."""
    services = sorted({record["svc"] for record in records})
    for name in P["files"]:
        mine = sorted((r for r in records if r["file"] == name), key=lambda r: r["t"])
        marked = set(rng.sample(range(len(mine)), min(traps, len(mine))))
        lines = [f"{P['comment']} log of {name[:-4]}, level names {' '.join(P['levels'])}"]
        for index, record in enumerate(mine):
            fake = dict(record, lvl=3, svc=rng.choice(services))
            if rng.random() < 0.02:
                lines.append(f"{P['comment']} rotated, {rng.randrange(2, 9)} segments kept")
            if index in marked and index % 2:
                lines.append(P["comment"] + _line(fake, "replayed entry", P))
            lines.append(_line(record, _message(rng, P), P))
            if index in marked and not index % 2:
                lines.append(rng.choice(["    ", "\t"]) + _line(fake, "nested report", P))
            elif rng.random() < 0.1:
                lines += [rng.choice(["    ", "  ", "\t"]) + rng.choice(TRACES) for _ in range(rng.randint(1, 3))]
        _util.write_text(root / "data" / name, "\n".join(lines) + "\n")


def _format_md(P):
    """FORMAT.md text: line format, rule parameters and the window list of the instance."""
    names = ", ".join(f"{canon}=`{name}`" for canon, name in zip(CANON, P["levels"]))
    rows = [f"| {_util.iso(w['start'])} | {_util.iso(w['end'])} | "
            + (f"`{w['service']}`" if w["service"] else "all services") + " |" for w in P["windows"]]
    lines = [
        "# FORMAT: service logs (this instance)", "",
        "Every parameter below belongs to this instance only. `example/` uses exactly the same rules.", "",
        "## Files",
        "- `data/*.log`: UTF-8 text. Each file is in time order, but the records of one service are"
        " spread over all files: put the records of all files together before computing gaps.",
        "", "## Kinds of line",
        f"- Comment prefix (JSON string): {json.dumps(P['comment'])}",
        "- A line that starts with the comment prefix (at column 0) is a comment. Ignore it.",
        "- A line that starts with a space or a tab is a continuation of the record above it. It is"
        " NOT a record of its own, whatever its text looks like. Ignore it.",
        "- Every other line is one record.",
        "", "## Record lines",
        f"- Separator (JSON string): {json.dumps(P['sep'])}",
        "- Field order: " + ", ".join(f"`{name}`" for name in P["order"]),
        "- The message is the last field and may itself contain the separator: split a record line"
        " at its first 3 separators only.",
        f"- Timestamp pattern: {P['ts']}",
        "- The pattern is in Python strptime notation, UTC (`epoch` means integer seconds since"
        f" 1970-01-01T00:00:00Z). Example: `{_util.fmt_ts(_util.EPOCH_2026 + 6254813, P['ts'])}` is"
        " 2026-03-14T09:26:53Z.",
        f"- Level names: {names}",
        "- A record is an ERROR record only when its level field equals the ERROR name exactly."
        " Words inside the message never count.",
    ]
    for name, seconds in P["correction"].items():
        lines.append(f"- Clock correction: add `{seconds}` seconds to every timestamp read from"
                     f" `data/{name}` (that clock was off) before using it for anything.")
    lines += [
        "", "## Maintenance windows",
        "Window times are UTC in ISO 8601, whatever the log timestamp pattern is.", "",
        "| start | end | applies to |", "|---|---|---|", *rows, "",
        f"- Window end: {'inclusive' if P['end_inclusive'] else 'exclusive'}",
        "- The start is always inclusive. `exclusive` end: a record at time t is inside when"
        " start <= t < end. `inclusive` end: inside when start <= t <= end.",
        "- A window that names a service applies only to records of that service; the others apply"
        " to every service.",
        "", "## Result",
        "- One entry per service that has at least one record line (also when it has no errors).",
        "- `errors`: the number of ERROR records of the service that are not inside any window that"
        " applies to it.",
        "- `max_gap_s`: sort those counted records by time; the largest difference in seconds between"
        " neighbours. 0 when there are fewer than two.",
    ]
    return "\n".join(lines) + "\n"


def generate(seed, workdir, level=2):
    """Write one logwin instance into workdir and return the hidden truth."""
    workdir, level = pathlib.Path(workdir), _util.clamp_level(level)
    P = _draw_params(_util.make_rng(FAMILY, seed, level, "params"), level)
    rng = _util.make_rng(FAMILY, seed, level, "main")
    count = {1: 300, 2: 380, 3: 460}[level] + rng.randrange(0, 41 if level == 1 else 91)
    calm = [s for s in P["services"] if s not in P["affected"]]
    records = _records(rng, P, P["services"], count, quiet=rng.choice(calm))
    answer = _truth(records, P)
    for attempt in range(200):
        ex_rng = _util.make_rng(FAMILY, seed, level, f"example{attempt}")
        ex_services = sorted(ex_rng.sample(P["affected"], min(2, len(P["affected"]))) + [ex_rng.choice(calm)])
        ex_records = _records(ex_rng, P, ex_services, 30)
        expected = _truth(ex_records, P)
        uncorrected = [dict(r, t=r["t"] - P["correction"].get(r["file"], 0)) for r in ex_records]
        if not _util.shares_pair(expected, answer) and (not P["correction"] or _truth(uncorrected, P) != expected):
            break
    _write_logs(workdir, rng, records, P, traps=2)
    _write_logs(workdir / "example", ex_rng, ex_records, P, traps=1)
    _util.write_text(workdir / "example" / "expected.json", json.dumps(expected, indent=1) + "\n")
    _util.write_text(workdir / "FORMAT.md", _format_md(P))
    _util.write_text(workdir / "TASK.md", TASK)
    return {"family": FAMILY, "level": level, "answer": answer, "params": P}


def check(workdir, truth, run_py=None):
    """Mean over truth services of 0.5 per correct field (errors, max_gap_s)."""
    try:
        answer = _util.load_json_file(pathlib.Path(workdir) / "answer.json")
        return _util.score_fields(answer, truth["answer"], ("errors", "max_gap_s"))
    except Exception:
        return 0.0


def _read_params(text):
    """Recover the rule parameters from FORMAT.md."""
    windows = []
    for start, end, scope in re.findall(r"^\| (\S+Z) \| (\S+Z) \| (.+?) \|$", text, re.M):
        windows.append({"start": _util.parse_ts(start, _util.TS_FORMATS[0]),
                        "end": _util.parse_ts(end, _util.TS_FORMATS[0]),
                        "service": scope.strip("`") if scope.startswith("`") else None})
    correction = {name: int(seconds) for seconds, name in
                  re.findall(r"^- Clock correction: add `(-?\d+)` seconds .*?`data/([^`]+)`", text, re.M)}
    return {
        "comment": json.loads(_util.grab(text, "Comment prefix (JSON string)")),
        "sep": json.loads(_util.grab(text, "Separator (JSON string)")),
        "order": re.findall(r"`(\w+)`", _util.grab(text, "Field order")),
        "ts": _util.grab(text, "Timestamp pattern"),
        "error": re.search(r"ERROR=`([^`]+)`", _util.grab(text, "Level names")).group(1),
        "end_inclusive": _util.grab(text, "Window end") == "inclusive",
        "windows": windows, "correction": correction,
    }


def _solve(workdir, sloppy=False):
    """Solve from the files alone. The sloppy variant ignores the maintenance windows and
    the clock correction, and parses continuation lines as if they were records."""
    workdir = pathlib.Path(workdir)
    P = _read_params((workdir / "FORMAT.md").read_text(encoding="utf-8"))
    errors = {}
    for path in sorted((workdir / "data").glob("*.log")):
        shift = 0 if sloppy else P["correction"].get(path.name, 0)
        for line in path.read_text(encoding="utf-8").split("\n"):
            if not line or line.startswith(P["comment"]):
                continue
            if line[0] in " \t":
                if not sloppy:
                    continue
                line = line.strip()
            parts = line.split(P["sep"], 3)
            if len(parts) < 4:
                continue
            fields = dict(zip(P["order"], parts))
            when = _util.parse_ts(fields["timestamp"], P["ts"]) + shift
            times = errors.setdefault(fields["service"], [])
            if fields["level"] == P["error"] and (sloppy or not _inside(when, fields["service"], P)):
                times.append(when)
    answer = {}
    for service, times in errors.items():
        times.sort()
        gaps = [later - earlier for earlier, later in zip(times, times[1:])]
        answer[service] = {"errors": len(times), "max_gap_s": max(gaps, default=0)}
    _util.write_text(workdir / "answer.json", json.dumps(answer, indent=1) + "\n")


def solve_from_files(workdir):
    """Reference solver: reads FORMAT.md and data/, writes the correct answer.json."""
    _solve(workdir)


def sloppy_solve(workdir):
    """Careless solver: no windows, no clock correction, continuation lines read as records."""
    _solve(workdir, sloppy=True)
