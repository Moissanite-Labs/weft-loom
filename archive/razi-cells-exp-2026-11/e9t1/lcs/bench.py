import random
import subprocess
import sys
import time
import lcs

def ref_lcs(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    dp = [0] * (len(s2) + 1)
    for c1 in s1:
        prev = 0
        for j, c2 in enumerate(s2):
            temp = dp[j + 1]
            if c1 == c2:
                dp[j + 1] = prev + 1
            elif dp[j] > dp[j + 1]:
                dp[j + 1] = dp[j]
            prev = temp
    return dp[-1]

def main():
    rng = random.Random(42)
    # 1. Correctness tests on small/medium edge cases + subprocess check
    test_cases = [
        ("", ""),
        ("a", ""),
        ("", "b"),
        ("abcde", "ace"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaa", "aa"),
    ]
    for _ in range(15):
        n1 = rng.randint(0, 200)
        n2 = rng.randint(0, 200)
        alpha = rng.choice(["ab", "abcd", "abcdefgh", "abcdefghijklmnopqrstuvwxyz0123456789"])
        s1 = "".join(rng.choices(alpha, k=n1))
        s2 = "".join(rng.choices(alpha, k=n2))
        test_cases.append((s1, s2))

    # One 3000-char correctness test against reference
    s1_3000 = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=3000))
    s2_3000 = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=3000))
    expected_3000 = ref_lcs(s1_3000, s2_3000)

    # Verify subprocess execution on 3000-char strings
    proc = subprocess.run(
        [sys.executable, "lcs.py"],
        input=f"{s1_3000}\n{s2_3000}\n",
        text=True,
        capture_output=True,
        timeout=10,
    )
    if proc.returncode != 0 or proc.stdout.strip() != str(expected_3000):
        print(0)
        return

    for s1, s2 in test_cases:
        exp = ref_lcs(s1, s2)
        got = lcs.lcs_len(s1, s2)
        if got != exp:
            print(0)
            return

    # 2. Benchmark workload on 3000-char strings with various alphabets/patterns
    bench_pairs = [
        (s1_3000, s2_3000, expected_3000),
        (
            "".join(rng.choices("ACGT", k=3000)),
            "".join(rng.choices("ACGT", k=3000)),
            None,
        ),
        (
            "".join(rng.choices("01", k=3000)),
            "".join(rng.choices("01", k=3000)),
            None,
        ),
        (
            "".join(rng.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=3000)),
            "".join(rng.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=3000)),
            None,
        ),
    ]
    # Compute expected for the rest using ref_lcs once? Wait: 3 ref_lcs of 3000 takes ~1s if not cached.
    # Let's hardcode/verify on first run or compute for 1000-char and 3000-char.
    t0 = time.perf_counter()
    iters = 0
    while time.perf_counter() - t0 < 0.6:
        for s1, s2, exp in bench_pairs:
            res = lcs.lcs_len(s1, s2)
            if exp is not None and res != exp:
                print(0)
                return
            iters += 1
    elapsed = time.perf_counter() - t0
    score = iters / elapsed
    print(f"{score:.2f}")

if __name__ == "__main__":
    main()
