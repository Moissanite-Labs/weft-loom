import subprocess
import sys
import time
import random
import lcs

def dp_lcs(a: str, b: str) -> int:
    # Classic O(N*M) DP for verification on small strings
    m, n = len(a), len(b)
    dp = [0] * (n + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b):
            temp = dp[j + 1]
            if ca == cb:
                dp[j + 1] = prev + 1
            elif dp[j] > dp[j + 1]:
                dp[j + 1] = dp[j]
            prev = temp
    return dp[n]

def verify():
    rng = random.Random(42)
    # Edge cases
    cases = [
        ("", ""),
        ("a", ""),
        ("", "a"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaaa", "aa"),
        ("abcbdab", "bdcaba"),
    ]
    for alpha in ["ab", "abcd", "abcdefgh", "abcdefghijklmnopqrstuvwxyz0123456789"]:
        for _ in range(15):
            la = rng.randint(0, 80)
            lb = rng.randint(0, 80)
            sa = "".join(rng.choices(alpha, k=la))
            sb = "".join(rng.choices(alpha, k=lb))
            cases.append((sa, sb))

    for sa, sb in cases:
        expected = dp_lcs(sa, sb)
        got = lcs.lcs(sa, sb)
        if got != expected:
            print(f"FAIL: {sa!r}, {sb!r} -> got {got}, expected {expected}", file=sys.stderr)
            return False

    # Also test CLI via subprocess on a couple cases
    p = subprocess.run([sys.executable, "lcs.py"], input="AGGTAB\nGXTXAYB\n", text=True, capture_output=True)
    if p.returncode != 0 or p.stdout.strip() != "4":
        print(f"CLI FAIL: {p.returncode} {p.stdout!r} {p.stderr!r}", file=sys.stderr)
        return False

    # Check Empty line CLI case
    p2 = subprocess.run([sys.executable, "lcs.py"], input="\nabc\n", text=True, capture_output=True)
    if p2.returncode != 0 or p2.stdout.strip() != "0":
        print(f"CLI empty line FAIL: {p2.stdout!r}", file=sys.stderr)
        return False

    return True

def benchmark():
    if not verify():
        print(0)
        return
    rng = random.Random(12345)
    alphabets = [
        "ACGT",
        "abcdefghijklmnopqrstuvwxyz",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "01",
    ]
    pairs = []
    # Pre-generate 20 pairs of 3000-char strings across different alphabets and similarity levels
    for i in range(20):
        alpha = alphabets[i % len(alphabets)]
        sa = "".join(rng.choices(alpha, k=3000))
        if i % 3 == 0:
            # High similarity (mutate 10%)
            sb_list = list(sa)
            for _ in range(300):
                idx = rng.randint(0, 2999)
                sb_list[idx] = rng.choice(alpha)
            sb = "".join(sb_list)
        else:
            sb = "".join(rng.choices(alpha, k=3000))
        pairs.append((sa, sb))

    # Check against reference bitwise implementation for 3000-char strings
    expected_sums = 0
    for sa, sb in pairs:
        m = len(sb)
        masks = {}
        for idx, ch in enumerate(sb):
            masks[ch] = masks.get(ch, 0) | (1 << idx)
        S = (1 << m) - 1
        for ch in sa:
            pm = masks.get(ch, 0)
            if pm:
                u = S & pm
                S = (S + u) | (S - u)
        ans = m - (S & ((1 << m) - 1)).bit_count()
        if lcs.lcs(sa, sb) != ans:
            print("FAIL on 3000-char verification", file=sys.stderr)
            print(0)
            return
        expected_sums += ans

    # Now time repeated evaluations so total runtime is ~0.5s
    t0 = time.perf_counter()
    iters = 0
    total = 0
    while True:
        for sa, sb in pairs:
            total += lcs.lcs(sa, sb)
        iters += 1
        el = time.perf_counter() - t0
        if el >= 0.4:
            break
    if total != expected_sums * iters:
        print(0)
        return
    ops_per_sec = (iters * len(pairs)) / el
    print(f"{ops_per_sec:.2f}")

if __name__ == "__main__":
    benchmark()
