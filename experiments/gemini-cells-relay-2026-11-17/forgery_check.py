#!/usr/bin/env python3
"""Look for any sign that a cell tried to forge a score or reach the referee.

The hidden tests of the two code families import the cell's code into the process that
prints the result line, so a harness or a solution could in principle print a result of
its own. This scans every harness snapshot and every build trace of the packed runs for
the words such an attempt would need. It proves nothing about attempts that left no text.

    python3 forgery_check.py > results/forgery_check.out
"""
import io
import re
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORDS = re.compile(r"nonce|hidden_check|\"passed\"\s*:|'passed'\s*:|sys\._getframe|inspect\.(stack|currentframe)|"
                   r"__main__\.|/cell/check|atexit|os\._exit|brain\.sock|cellapi\._rpc|\bptrace\b|/proc/\d", re.I)


def main() -> int:
    hits, files = [], 0
    for arch in sorted((HERE / "results" / "runs").glob("*/artifacts.tar.gz")):
        with tarfile.open(arch) as tar:
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                files += 1
                text = tar.extractfile(m).read().decode("utf-8", "replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if WORDS.search(line):
                        hits.append(f"{arch.parent.name}/{m.name}:{i}: {line.strip()[:160]}")
    print(f"scanned {files} files in {len(list((HERE / 'results' / 'runs').glob('*/artifacts.tar.gz')))} runs")
    print(f"{len(hits)} lines match")
    for h in hits:
        print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
