#!/usr/bin/env python3
"""Print the ten most frequent ASCII words from stdin.

Words are maximal runs of ASCII letters.  They are case-folded to lowercase
before counting, and any other byte acts as a separator.  Results are ordered
by descending count, then ascending word.
"""
import sys
from collections import Counter
from heapq import nsmallest

# Translate uppercase ASCII to lowercase and every non-letter byte to a space.
_TR = bytearray(b" " * 256)
for _c in range(97, 123):
    _TR[_c] = _c
for _c in range(65, 91):
    _TR[_c] = _c + 32
_TABLE = bytes(_TR)


def main() -> None:
    data = sys.stdin.buffer.read()
    if not data:
        return
    counts = Counter(data.translate(_TABLE).split())
    if not counts:
        return
    top = nsmallest(10, counts.items(), key=lambda x: (-x[1], x[0]))
    out = b"".join(w + b" " + str(n).encode() + b"\n" for w, n in top)
    sys.stdout.buffer.write(out)


if __name__ == "__main__":
    main()
