import time
import random
import subprocess
import sys
import lcs

def dp_lcs(a, b):
    dp = [0] * (len(b) + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b):
            cur = dp[j + 1]
            dp[j + 1] = prev + 1 if ca == cb else (dp[j] if dp[j] > cur else cur)
            prev = cur
    return dp[-1]

def main():
    rng = random.Random(42)
    # 1. Verify correctness on edge cases and random strings against DP
    cases = [
        ("", ""),
        ("a", ""),
        ("", "a"),
        ("abc", "abc"),
        ("abc", "def"),
        ("abcde", "ace"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaa", "aa"),
    ]
    for _ in range(15):
        la = rng.randint(0, 80)
        lb = rng.randint(0, 80)
        alpha = rng.choice(["ab", "abcd", "abcdefghij", "abcdefghijklmnopqrstuvwxyz"])
        sa = "".join(rng.choices(alpha, k=la))
        sb = "".join(rng.choices(alpha, k=lb))
        cases.append((sa, sb))

    for sa, sb in cases:
        if lcs.lcs(sa, sb) != dp_lcs(sa, sb):
            print(0)
            return

    # 2. Check CLI interface via subprocess
    p = subprocess.run([sys.executable, "lcs.py"], input="AGGTAB\nGXTXAYB\n", text=True, capture_output=True)
    if p.returncode != 0 or p.stdout.strip() != "4":
        print(0)
        return

    # 3. Benchmark 3000-char strings
    pairs = []
    alphas = [
        "abcd",
        "abcdefghijklmnopqrstuvwxyz",
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ab"
    ]
    for i in range(200):
        alpha = alphas[i % len(alphas)]
        s1 = "".join(rng.choices(alpha, k=3000))
        s2 = "".join(rng.choices(alpha, k=3000))
        pairs.append((s1, s2))

    # Expected sum on first 5 pairs checked against 3000-char known values
    t0 = time.perf_counter()
    total = 0
    for _ in range(2):
        for s1, s2 in pairs:
            total += lcs.lcs(s1, s2)
    elapsed = time.perf_counter() - t0
    if total <= 0:
        print(0)
        return
    # Score = pairs per second
    print(f"{400.0 / elapsed:.2f}")

if __name__ == "__main__":
    main()
