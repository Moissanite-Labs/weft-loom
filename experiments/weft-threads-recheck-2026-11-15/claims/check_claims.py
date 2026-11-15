#!/usr/bin/env python3
"""Check sentences in the notes against the data files they rest on.

A result in this record has a second program checking it. A sentence has
nobody, and the review findings counted in ../review-meta.md are mostly
sentences that drifted from the files beside them. This program is the second
check for sentences. Each entry of claims.json names a note, a piece of text
that must appear in it, and a test on a data file. If the text is gone from
the note, or the data no longer supports it, the run stops with a non-zero
exit status. So a sentence cannot outlive its evidence without someone seeing.

Paths in claims.json are relative to the experiments/ folder of the checkout.

Kinds of test:
  json      {"file", "path": [keys or indexes], "equals"}         a value in a JSON file
            optional "round": n compares round(value, n); "sig": n compares to n significant digits
  jsoncount {"file", "path": [keys to a list], "where": {key: value}, "equals"}
            the number of entries of a list whose fields equal the given values
  line      {"file", "contains"}                                   some line of a text file contains this text
  count     {"file", "pattern", "equals"}                          lines of a text file that contain a pattern
  tsvcount  {"file", "where": {column: value}, "equals"}           rows of a tab-separated file with these values
  files     {"glob", "equals"}                                     files matching a pattern

Usage: python3 check_claims.py [experiments folder]
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parents[1]


def get(obj, path):
    for k in path:
        obj = obj[k]
    return obj


def run_test(t):
    """Return None if the test holds, otherwise a sentence saying why not."""
    kind = t["kind"]
    if kind == "json":
        v = get(json.loads((ROOT / t["file"]).read_text()), t["path"])
        if "round" in t:
            v = round(v, t["round"])
        if "sig" in t:
            v = float(f"{v:.{t['sig']}g}")
        if v != t["equals"]:
            return f"{t['file']} gives {v!r}, the note needs {t['equals']!r}"
    elif kind == "jsoncount":
        rows = get(json.loads((ROOT / t["file"]).read_text()), t.get("path", []))
        n = sum(1 for r in rows if all(r.get(k) == v for k, v in t.get("where", {}).items()))
        if n != t["equals"]:
            return f"{n} entries of {t['file']} match {t.get('where', {})}, the note needs {t['equals']}"
    elif kind == "line":
        text = (ROOT / t["file"]).read_text(encoding="utf-8", errors="replace")
        if not any(t["contains"] in line for line in text.splitlines()):
            return f"no line of {t['file']} contains \"{t['contains']}\""
    elif kind == "count":
        text = (ROOT / t["file"]).read_text(encoding="utf-8", errors="replace")
        n = sum(1 for line in text.splitlines() if t["pattern"] in line)
        if n != t["equals"]:
            return f"{n} lines of {t['file']} contain \"{t['pattern']}\", the note needs {t['equals']}"
    elif kind == "tsvcount":
        with (ROOT / t["file"]).open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        n = sum(1 for r in rows if all(r.get(k) == v for k, v in t.get("where", {}).items()))
        if n != t["equals"]:
            return f"{n} rows of {t['file']} match {t.get('where', {})}, the note needs {t['equals']}"
    elif kind == "files":
        n = len(glob.glob(str(ROOT / t["glob"])))
        if n != t["equals"]:
            return f"{n} files match {t['glob']}, the note needs {t['equals']}"
    else:
        return f"unknown kind of test {kind}"
    return None


def main():
    claims = json.loads((HERE / "claims.json").read_text())
    bad = 0
    for c in claims:
        note = ROOT / c["note"]
        label = f"{c['note']}: \"{c['text'][:64]}\""
        if not note.is_file():
            why = "note not found"
        elif c["text"] not in note.read_text(encoding="utf-8"):
            why = "the text is no longer in the note"
        else:
            try:
                why = run_test(c["test"])
            except (OSError, KeyError, IndexError, ValueError, TypeError) as e:
                why = f"could not run the test: {type(e).__name__}: {e}"
        if why:
            bad += 1
            print(f"FAIL  {label}  ->  {why}")
        else:
            print(f"ok    {label}")
    print(f"{len(claims) - bad} of {len(claims)} claims hold")
    if bad or not claims:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
