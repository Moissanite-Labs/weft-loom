#!/usr/bin/env python3
"""Write the SHA-256 of every file part A runs or is analysed with into the section
"Frozen files" of block2/PLAN.md. `run.py assay2` refuses to start if any of them differs,
and an approval names the hash of the whole plan, so changing any of these files after an
approval needs a new approval. Run from the record folder:

    python3 -I -B block2/freeze.py           # rewrite the section
    python3 -I -B block2/freeze.py --check   # exit 1 if the section is out of date
"""

import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
PLAN = HERE / "block2" / "PLAN.md"
PATTERNS = ("run.py", "block2/analyze_a.py", "referee/*.py", "referee/tasks/*.py", "seed/*", "seed/tools/*")


def frozen_files():
    files = set()
    for pattern in PATTERNS:
        files.update(p for p in HERE.glob(pattern) if p.is_file() and "__pycache__" not in p.parts)
    return sorted(files)


def section():
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(HERE).as_posix()}" for p in frozen_files()]
    return ("Written by `block2/freeze.py`. `run.py assay2` checks every line before it starts.\n\n```\n"
            + "\n".join(lines) + "\n```\n")


def main(argv):
    text = PLAN.read_text()
    pattern = re.compile(r"(^## Frozen files[^\n]*\n\n)(.*?)(?=^## |\Z)", re.M | re.S)
    m = pattern.search(text)
    if not m:
        raise SystemExit("PLAN.md has no section '## Frozen files'")
    new = text[:m.start(2)] + section() + ("\n" if m.end() < len(text) else "") + text[m.end():]
    if argv[:1] == ["--check"]:
        if new != text:
            print("block2/PLAN.md: the frozen-file hashes are out of date")
            return 1
        print("block2/PLAN.md: the frozen-file hashes match")
        return 0
    PLAN.write_text(new)
    print(f"wrote {len(frozen_files())} hashes into block2/PLAN.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
