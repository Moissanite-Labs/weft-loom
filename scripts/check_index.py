#!/usr/bin/env python3
"""Every record and every note is listed in its index, with a status.

experiments/README.md must link each folder in experiments/, and notes/README.md
must link each Markdown file in notes/ (supporting folders such as notes/assets/
are not indexed). The index line that holds the link must carry one status from
the vocabulary below, written in backticks, so a reader can tell a finished
result from a pilot or an idea without opening the record.

Exit status: 0 when every entry is indexed with a status, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RECORD_STATUSES = frozenset(
    {"complete", "partial", "pilot", "exploratory", "design", "withdrawn", "superseded"}
)
NOTE_STATUSES = frozenset({"idea", "proposal", "adopted", "superseded", "withdrawn"})

LINK = re.compile(r"\]\(\s*(?:\./)?([^)#\s]+?)/?\s*(?:#[^)]*)?\)")
STATUS = re.compile(r"`([a-z]+)`")


def index_lines(index: Path) -> dict[str, str]:
    """Map each relative link target in the index to the line that holds it."""
    found: dict[str, str] = {}
    if not index.is_file():
        return found
    for line in index.read_text(encoding="utf-8").splitlines():
        for target in LINK.findall(line):
            found.setdefault(target.rstrip("/"), line)
    return found


def check(entries: list[str], index: Path, statuses: frozenset[str]) -> list[str]:
    problems = []
    lines = index_lines(index)
    rel = index.relative_to(ROOT) if index.is_relative_to(ROOT) else index
    for name in entries:
        line = lines.get(name)
        if line is None:
            problems.append(f"{rel}: no entry links {name}")
            continue
        if not set(STATUS.findall(line)) & statuses:
            allowed = ", ".join(sorted(statuses))
            problems.append(f"{rel}: the entry for {name} has no status (one of: {allowed})")
    return problems


def record_folders(root: Path = ROOT) -> list[str]:
    base = root / "experiments"
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith((".", "__")))


def note_files(root: Path = ROOT) -> list[str]:
    base = root / "notes"
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.glob("*.md") if p.name != "README.md")


def main() -> int:
    problems = check(record_folders(), ROOT / "experiments" / "README.md", RECORD_STATUSES)
    problems += check(note_files(), ROOT / "notes" / "README.md", NOTE_STATUSES)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print("Add a row to the index with a status in backticks. See CONTRIBUTING.md.", file=sys.stderr)
        return 1
    print(f"index check: {len(record_folders())} records and {len(note_files())} notes indexed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
