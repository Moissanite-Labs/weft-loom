import os
import random
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lcs import lcs_length


def dp(a, b):
    if len(a) < len(b):
        a, b = b, a
    m = len(b)
    prev = [0] * (m + 1)
    for ch in a:
        cur = [0] * (m + 1)
        for j in range(m):
            if ch == b[j]:
                cur[j + 1] = prev[j] + 1
            else:
                x = cur[j]
                y = prev[j + 1]
                cur[j + 1] = x if x > y else y
        prev = cur
    return prev[m]


def rbytes(rng, n, k):
    return bytes(rng.randrange(97, 97 + k) for _ in range(n))


def main():
    rng = random.Random(20240117)
    ok = True

    # --- 1. correctness vs plain DP on small/medium inputs -----------------
    cases = []
    for k, n, m in ((2, 200, 180), (4, 220, 220), (26, 200, 250), (3, 150, 300)):
        cases.append((rbytes(rng, n, k), rbytes(rng, m, k)))
    cases.append((b"", b""))
    cases.append((b"abcdef", b""))
    cases.append((b"", b"xyz"))
    cases.append((b"aaaa", b"aaaa"))
    cases.append((b"abcabcabc", b"cbacbacba"))
    cases.append((b"the quick brown fox", b"the lazy brown dog"))
    cases.append((b"\x00\x01\x02\x01", b"\x01\x02\x00\x01\x02"))
    cases.append((b"x" * 300, b"y" * 300))
    for a, b in cases:
        want = dp(a, b)
        got = lcs_length(a, b)
        if got != want:
            sys.stderr.write("DP mismatch %r %r want=%d got=%d\n" % (a[:40], b[:40], want, got))
            ok = False

    # --- 2. full-size structural checks ------------------------------------
    big = rbytes(rng, 3000, 26)
    checks = [
        (big, big, 3000),
        (big, big[::2], 1500),
        (big, big[:1500], 1500),
        (big, bytes((c + 1) if c < 122 else 97 for c in big), None),
        (rbytes(rng, 3000, 2), rbytes(rng, 3000, 2), None),
    ]
    for a, b, want in checks:
        got = lcs_length(a, b)
        if want is not None:
            if got != want:
                sys.stderr.write("struct fail want=%d got=%d\n" % (want, got))
                ok = False
        if got > min(len(a), len(b)):
            sys.stderr.write("bound fail\n")
            ok = False
    # disjoint alphabets -> 0
    if lcs_length(rbytes(rng, 3000, 3), bytes(97 + 10 + (i % 3) for i in range(3000))) != 0:
        sys.stderr.write("disjoint fail\n")
        ok = False

    # --- 3. I/O path via the real program ---------------------------------
    a = rbytes(rng, 500, 5)
    b = rbytes(rng, 520, 5)
    want = dp(a, b)
    try:
        out = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lcs.py")],
            input=a + b"\r\n" + b + b"\r\n",
            stdout=subprocess.PIPE,
            timeout=60,
        ).stdout
    except Exception as exc:  # noqa
        sys.stderr.write("io error %r\n" % (exc,))
        out = b""
    try:
        got = int(out.split()[0])
    except Exception:
        got = -1
    if got != want:
        sys.stderr.write("io mismatch want=%d got=%r\n" % (want, out[:60]))
        ok = False

    if not ok:
        print(0)
        return

    # --- 4. timing block (heavy) ------------------------------------------
    pairs = []
    for k in (2, 4, 26):
        for _ in range(12):
            pairs.append((rbytes(rng, 3000, k), rbytes(rng, 3000, k)))

    best = None
    for _ in range(3):
        t0 = time.perf_counter()
        acc = 0
        for a, b in pairs:
            acc += lcs_length(a, b)
        dt = time.perf_counter() - t0
        if best is None or dt < best:
            best = dt
    print(round(1000.0 / best, 3))


main()
