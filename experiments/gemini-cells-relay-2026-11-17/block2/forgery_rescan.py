#!/usr/bin/env python3
"""A second scan of the pilot's packed runs, for the two forgeries that
block2/checker_equivalence.py showed the pilot's checker would have accepted: calling the
hidden script's reporting function, and returning an object equal to everything. The first
scan (forgery_check.py) already looked for `__main__.`, the nonce and os._exit; this adds
the remaining words those forgeries need. It reads harness snapshots and build traces. The
code that solving cells wrote during episodes was not kept by the pilot, so it is not
covered, except where a builder printed it into its own trace.

    python3 -I -B block2/forgery_rescan.py > block2/forgery_rescan.out
"""
import re
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
# MODULES, TESTS and the helper names are matched case-sensitively, as the hidden script spells
# them; the rest in any case.
WORDS = re.compile(r"(?i:__eq__|__ne__|__hash__|import\s+__main__|sys\.modules\[\s*['\"]__main__)|"
                   r"\bfinish\s*\(|\bMODULES\b|\bTESTS\b|\b_holds\b|\b_passes\b|\bguarded\s*\(")


def main() -> int:
    hits, files = [], 0
    for arch in sorted((HERE / "results" / "runs").glob("*/artifacts.tar.gz")):
        with tarfile.open(arch) as tar:
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                files += 1
                text = tar.extractfile(m).read().decode("utf-8", "replace")
                for n, line in enumerate(text.splitlines(), 1):
                    if WORDS.search(line):
                        hits.append(f"{arch.parent.name}/{m.name}:{n}: {line.strip()[:160]}")
    print(f"scanned {files} files in {len(list((HERE / 'results' / 'runs').glob('*/artifacts.tar.gz')))} runs")
    print(f"{len(hits)} lines match")
    for h in hits:
        print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
