import subprocess
import sys
import time
import random
import lcs

def lcs_dp(a, b):
    dp = [0] * (len(b) + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b):
            cur = dp[j + 1]
            if ca == cb:
                dp[j + 1] = prev + 1
            elif dp[j] > dp[j + 1]:
                dp[j + 1] = dp[j]
            prev = cur
    return dp[-1]

def verify():
    rng = random.Random(42)
    cases = [
        ("", ""),
        ("a", ""),
        ("", "b"),
        ("a", "a"),
        ("abc", "def"),
        ("abcde", "ace"),
        ("aaaaa", "aa"),
        ("abcbdab", "bdcaba"),
    ]
    for a, b in cases:
        if lcs.lcs(a, b) != lcs_dp(a, b):
            return False
    for n, m, alpha in [(20, 20, "ab"), (50, 40, "abcd"), (100, 120, "abcdefghij"), (200, 200, "abcdefghijklmnopqrstuvwxyz")]:
        a = "".join(rng.choice(alpha) for _ in range(n))
        b = "".join(rng.choice(alpha) for _ in range(m))
        if lcs.lcs(a, b) != lcs_dp(a, b):
            return False
    a3000 = "".join(rng.choice("abcd") for _ in range(3000))
    b3000 = "".join(rng.choice("abcd") for _ in range(3000))
    out = subprocess.check_output([sys.executable, "lcs.py"], input=f"{a3000}\n{b3000}\n".encode()).decode().strip()
    if int(out) != lcs.lcs(a3000, b3000) or int(out) != lcs_dp(a3000, b3000):
        return False
    return True

def main():
    if not verify():
        print(0)
        return
    rng = random.Random(123)
    pairs = []
    for alpha in ["ab", "abcd", "abcdefgh", "abcdefghijklmnopqrstuvwxyz", "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
        for _ in range(6):
            a = "".join(rng.choice(alpha) for _ in range(3000))
            b = "".join(rng.choice(alpha) for _ in range(3000))
            pairs.append((a, b))
    expected = sum(lcs.lcs(a, b) for a, b in pairs)
    best_ops = 0.0
    iters = 4
    for _ in range(7):
        t0 = time.perf_counter()
        total = 0
        for _ in range(iters):
            for a, b in pairs:
                total += lcs.lcs(a, b)
        dt = time.perf_counter() - t0
        if total != iters * expected:
            print(0)
            return
        ops = (iters * len(pairs)) / dt
        if ops > best_ops:
            best_ops = ops
    print(f"{best_ops:.2f}")

if __name__ == "__main__":
    main()
