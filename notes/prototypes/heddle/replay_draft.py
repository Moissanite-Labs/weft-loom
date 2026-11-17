#!/usr/bin/env python3
"""Check a draft exported by the instrument, without the instrument.

    python3 replay_draft.py sample-draft.json
    python3 replay_draft.py my-session.json        (paste from the page's "Copy draft")

Rebuilds every fell from the seed and the recorded moves, recomputes each weight root, runs
the port of weft's gate, re-derives the probes from each root, and re-reads each claim. A
snap is checked from its one witness input. Exit status 0 when nothing differs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heddle as hd  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    draft = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    problems = hd.replay_draft(draft)
    events = draft.get("events", [])
    kinds = {k: sum(1 for e in events if e.get("kind") == k) for k in ("pick", "snap", "unpick")}
    print(f"{len(events)} events: {kinds['pick']} picks, {kinds['snap']} snaps, {kinds['unpick']} unpicks")
    if problems:
        for p in problems:
            print("DIFFERS:", p)
        return 1
    print("every root, verdict, witness and reading checks out")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
