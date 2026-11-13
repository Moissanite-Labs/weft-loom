import random
import subprocess
import sys
import time
import lcs

def ref_lcs(a: str, b: str) -> int:
    if not a or not b:
        return 0
    m = len(b)
    masks = {}
    for i, ch in enumerate(b):
        masks[ch] = masks.get(ch, 0) | (1 << i)
    S = (1 << m) - 1
    for ch in a:
        pm = masks.get(ch, 0)
        u = S & pm
        S = (S + u) | (S - u)
    return (~S & ((1 << m) - 1)).bit_count()

def ref_dp(a: str, b: str) -> int:
    dp = [0] * (len(b) + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b):
            cur = dp[j + 1]
            if ca == cb:
                dp[j + 1] = prev + 1
            elif dp[j] > cur:
                dp[j + 1] = dp[j]
            prev = cur
    return dp[-1]

def verify():
    # Edge cases and random cases
    cases = [
        ("", "", 0),
        ("a", "", 0),
        ("", "b", 0),
        ("abc", "abc", 3),
        ("abc", "def", 0),
        ("AGGTAB", "GXTXAYB", 4),
        ("aaaa", "aa", 2),
        ("abcbdab", "bdcaba", 4),
    ]
    for a, b, exp in cases:
        got = lcs.lcs_length(a, b)
        if got != exp:
            print(f"FAIL case ({a!r}, {b!r}): got {got}, expected {exp}", file=sys.stderr)
            return False

    # Check subprocess CLI interface
    res = subprocess.run(
        [sys.executable, "lcs.py"],
        input="AGGTAB\nGXTXAYB\n",
        text=True,
        capture_output=True,
        timeout=5,
    )
    if res.returncode != 0 or res.stdout.strip() != "4":
        print(f"FAIL subprocess: rc={res.returncode} out={res.stdout!r}", file=sys.stderr)
        return False

    rng = random.Random(42)
    alphabets = [
        "ACGT",
        "abcdefghijklmnopqrstuvwxyz",
        "01",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    ]
    test_pairs = []
    for alpha in alphabets:
        for n, m in [(50, 50), (200, 150), (3000, 3000)]:
            a = "".join(rng.choices(alpha, k=n))
            b = "".join(rng.choices(alpha, k=m))
            exp = ref_dp(a, b) if n < 500 else ref_lcs(a, b)
            got = lcs.lcs_length(a, b)
            if got != exp:
                print(f"FAIL random len=({n},{m}) alpha={len(alpha)}: got {got}, exp {exp}", file=sys.stderr)
                return False
            if n == 3000:
                test_pairs.append((a, b, exp))

    # Also test identical, reversed, and partially shared 3000-char strings
    s3000 = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=3000))
    test_pairs.append((s3000, s3000, 3000))
    s3000_rev = s3000[::-1]
    test_pairs.append((s3000, s3000_rev, ref_lcs(s3000, s3000_rev)))

    # Verify one 3000-char pair via subprocess stdin
    a0, b0, exp0 = test_pairs[0]
    res = subprocess.run(
        [sys.executable, "lcs.py"],
        input=f"{a0}\n{b0}\n",
        text=True,
        capture_output=True,
        timeout=10,
    )
    if res.returncode != 0 or int(res.stdout.strip()) != exp0:
        print("FAIL subprocess 3000", file=sys.stderr)
        return False

    return test_pairs

def main():
    test_pairs = verify()
    if not test_pairs:
        print(0)
        sys.exit(1)

    # Benchmark on 3000-char string pairs for ~0.5 seconds
    t0 = time.perf_counter()
    iters = 0
    while True:
        for a, b, exp in test_pairs:
            if lcs.lcs_length(a, b) != exp:
                print(0)
                sys.exit(1)
            iters += 1
        elapsed = time.perf_counter() - t0
        if elapsed >= 0.45:
            break

    ops_per_sec = iters / elapsed
    print(f"{ops_per_sec:.2f}")

if __name__ == "__main__":
    main()
