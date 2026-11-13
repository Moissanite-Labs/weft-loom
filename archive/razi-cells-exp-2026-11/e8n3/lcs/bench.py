import subprocess
import sys
import time
import random
import lcs

def dp_lcs(a, b):
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
    # Edge cases via subprocess and direct call
    cases = [
        ("", ""),
        ("a", ""),
        ("", "b"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaaa", "aa"),
        ("ab" * 50, "ba" * 50),
    ]
    rng = random.Random(123)
    for _ in range(20):
        la = rng.randint(0, 80)
        lb = rng.randint(0, 80)
        alpha = rng.choice(["ab", "abcd", "abcdefgh", "0123456789abcdefghijklmnopqrstuvwxyz"])
        a = "".join(rng.choices(alpha, k=la))
        b = "".join(rng.choices(alpha, k=lb))
        cases.append((a, b))

    for a, b in cases:
        exp = dp_lcs(a, b)
        got = lcs.lcs_len(a, b)
        if got != exp:
            print(0)
            sys.exit(0)

    # Also test CLI via subprocess on a 3000-char pair
    a3000 = "".join(rng.choices("abcdefgh", k=3000))
    b3000 = "".join(rng.choices("abcdefgh", k=3000))
    p = subprocess.run([sys.executable, "lcs.py"], input=f"{a3000}\n{b3000}\n", text=True, capture_output=True)
    if p.returncode != 0 or int(p.stdout.strip()) != lcs.lcs_len(a3000, b3000):
        print(0)
        sys.exit(0)
    # Test CLI with empty line
    p2 = subprocess.run([sys.executable, "lcs.py"], input="\nabc\n", text=True, capture_output=True)
    if p2.returncode != 0 or int(p2.stdout.strip()) != 0:
        print(0)
        sys.exit(0)

    # Generate workload of 3000-char string pairs (diverse alphabets and similarities)
    pairs = []
    for i in range(200):
        alpha = ["ACGT", "abcdefgh", "abcdefghijklmnopqrstuvwxyz", "01"][i % 4]
        s1 = "".join(rng.choices(alpha, k=3000))
        s2 = "".join(rng.choices(alpha, k=3000))
        pairs.append((s1, s2))

    t0 = time.perf_counter()
    iters = 0
    total = 0
    for _ in range(3):
        for s1, s2 in pairs:
            total += lcs.lcs_len(s1, s2)
            iters += 1
    dt = time.perf_counter() - t0
    if total != 3 * 343841:
        print(f"CHECKSUM={total // 3}", file=sys.stderr)
        print(0)
        sys.exit(0)
    # Pairs per second
    print(f"{iters / dt:.2f}")

if __name__ == "__main__":
    verify()
