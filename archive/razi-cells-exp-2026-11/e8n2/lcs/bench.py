import random
import subprocess
import sys
import time
import lcs

def dp_lcs(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [0] * (n + 1)
    for c1 in s1:
        prev = 0
        for j, c2 in enumerate(s2):
            temp = dp[j + 1]
            if c1 == c2:
                dp[j + 1] = prev + 1
            else:
                if dp[j] > dp[j + 1]:
                    dp[j + 1] = dp[j]
            prev = temp
    return dp[n]

def verify():
    rng = random.Random(42)
    cases = [
        ("", ""),
        ("a", ""),
        ("", "b"),
        ("abcde", "ace"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaa", "aa"),
    ]
    for alphabet in ["ab", "abcd", "abcdefghijklmnopqrstuvwxyz", "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
        for _ in range(10):
            l1 = rng.randint(0, 150)
            l2 = rng.randint(0, 150)
            s1 = "".join(rng.choices(alphabet, k=l1))
            s2 = "".join(rng.choices(alphabet, k=l2))
            cases.append((s1, s2))

    for s1, s2 in cases:
        expected = dp_lcs(s1, s2)
        got = lcs.lcs_length(s1, s2)
        if got != expected:
            print(0)
            sys.exit(0)

    # Also test CLI via subprocess
    p = subprocess.run([sys.executable, "lcs.py"], input="AGGTAB\nGXTXAYB\n", text=True, capture_output=True)
    if p.returncode != 0 or p.stdout.strip() != "4":
        print(0)
        sys.exit(0)

def benchmark():
    rng = random.Random(12345)
    alphabets = [
        "ACGT",
        "abcdefghijklmnopqrstuvwxyz",
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    ]
    pairs = []
    for i in range(60):
        alpha = alphabets[i % len(alphabets)]
        s1 = "".join(rng.choices(alpha, k=3000))
        s2 = "".join(rng.choices(alpha, k=3000))
        pairs.append((s1, s2))

    # Sanity check first pair against DP
    if lcs.lcs_length(*pairs[0]) != dp_lcs(*pairs[0]):
        print(0)
        sys.exit(0)

    # Warmup
    for s1, s2 in pairs[:5]:
        lcs.lcs_length(s1, s2)

    t0 = time.perf_counter()
    iters = 0
    while time.perf_counter() - t0 < 0.6:
        for s1, s2 in pairs:
            lcs.lcs_length(s1, s2)
        iters += len(pairs)
    elapsed = time.perf_counter() - t0
    # Score = pairs per second
    print(f"{iters / elapsed:.2f}")

if __name__ == "__main__":
    verify()
    benchmark()
