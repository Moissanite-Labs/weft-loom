#!/usr/bin/env python3
"""Independent correctness and throughput check for wf.py.

The generated corpus is exactly 20,000,000 bytes.  Canonical words are
maximal ASCII alphabetic runs in the lowercased byte stream; every other byte
is a separator.  The expected answer is computed with a separate regex-based
implementation, including a deliberate tie at the tenth position.
"""
import os
import random
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WF = ROOT / "wf.py"
CACHE = Path(os.environ.get("WF_CACHE_DIR", "/tmp"))
CORPUS = CACHE / "wf_colony_corpus_v1.bin"
EXPECTED = CACHE / "wf_colony_expected_v1.txt"
TARGET = 20_000_000
REPEATS = 200
BLOCK_LEN = TARGET // REPEATS
BENCH_REPEATS = 3
WORD_RE = re.compile(rb"[a-z]+")


def format_top(counts):
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return b"".join(w + b" " + str(n).encode() + b"\n" for w, n in top)


def canonical(data):
    return format_top(Counter(WORD_RE.findall(data.lower())))


def make_name(i):
    return b"word" + bytes((97 + i // 26, 97 + i % 26))


def make_corpus():
    rng = random.Random(20240617)
    words = [make_name(i) for i in range(200)]
    weighted = []
    for i in range(8):
        weighted += [words[i]] * (60 - 4 * i)
    for i in range(8, 12):
        weighted += [words[i]] * 28
    for i, word in enumerate(words[12:]):
        weighted += [word] * (1 + i % 9)

    separators = [
        b" ", b"  ", b"\n", b"\t", b", ", b"; ", b". ", b"! ",
        b"? ", b"-- ", b"42 ", b"\xc3\xa9 ", b"\x00 ", b"' ",
    ]
    unit = bytearray()
    while True:
        batch = weighted[:]
        rng.shuffle(batch)
        piece = bytearray()
        for word in batch:
            for c in word:
                piece.append(c - 32 if rng.random() < 0.18 else c)
            piece.extend(rng.choice(separators))
        if len(unit) + len(piece) > BLOCK_LEN:
            break
        unit.extend(piece)
    if not unit or len(unit) > BLOCK_LEN:
        raise RuntimeError("bad generated unit")
    unit.extend(b" " * (BLOCK_LEN - len(unit)))
    block = bytes(unit)

    CACHE.mkdir(parents=True, exist_ok=True)
    with CORPUS.open("wb") as f:
        for _ in range(REPEATS):
            f.write(block)

    # Compute from the entire corpus, not from the generator's internal counts.
    with CORPUS.open("rb") as f:
        expected = canonical(f.read())
    EXPECTED.write_bytes(expected)
    return expected


def ensure_corpus():
    if (not CORPUS.exists() or CORPUS.stat().st_size != TARGET
            or not EXPECTED.exists()):
        return make_corpus()
    return EXPECTED.read_bytes()


def run_wf(data):
    try:
        p = subprocess.run(
            [sys.executable, str(WF)], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
        )
    except Exception as e:
        print(f"wf.py failed to run: {e}", file=sys.stderr)
        return None
    if p.returncode:
        print(f"wf.py exited {p.returncode}: {p.stderr[:400]!r}", file=sys.stderr)
        return None
    return p.stdout


def edge_cases():
    cases = [
        b"",
        b"123 !!! \x00\xff\n\t",
        b"a A a\nB b, b2c can't \xc3\xa9",
        b"Zz zz apple apple banana Banana CHERRY cherry cherry",
        b"x y z q r s t u v w a b c d e f g h i j\n",
        b"one TWO three four five six seven eight nine ten eleven",
        b"a-b_c9d e.\xf0\x9f\x98\x80f",
        b"aa " * 7 + b"bb " * 7 + b"cc " * 6 + b"dd " * 6,
        b"word",
        b" leading and trailing separators !!! ",
    ]
    for i, data in enumerate(cases):
        want = canonical(data)
        got = run_wf(data)
        if got != want:
            print(f"edge case {i} failed: want {want!r}, got {got!r}", file=sys.stderr)
            return False
    return True


def main():
    expected = ensure_corpus()
    if not edge_cases():
        print("0")
        return

    times = []
    for _ in range(BENCH_REPEATS):
        with CORPUS.open("rb") as f:
            t0 = time.perf_counter()
            try:
                p = subprocess.run(
                    [sys.executable, str(WF)], stdin=f,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
                )
            except Exception as e:
                print(f"benchmark failed: {e}", file=sys.stderr)
                print("0")
                return
            dt = time.perf_counter() - t0
        if p.returncode or p.stdout != expected:
            print(
                f"20MB output mismatch (rc={p.returncode}, "
                f"stderr={p.stderr[:200]!r})", file=sys.stderr,
            )
            print("0")
            return
        times.append(dt)
    mb_per_sec = (TARGET / 1_000_000) * len(times) / sum(times)
    print(f"{mb_per_sec:.3f}")


if __name__ == "__main__":
    main()
