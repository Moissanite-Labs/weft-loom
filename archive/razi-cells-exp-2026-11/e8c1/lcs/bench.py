import time
import random
import subprocess
import sys
import lcs

def dp_lcs(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = [0] * (n + 1)
    for ch_a in a:
        prev = 0
        for j, ch_b in enumerate(b):
            temp = dp[j + 1]
            if ch_a == ch_b:
                dp[j + 1] = prev + 1
            elif dp[j] > dp[j + 1]:
                dp[j + 1] = dp[j]
            prev = temp
    return dp[n]

def verify():
    # Edge cases
    cases = [
        ("", ""),
        ("a", ""),
        ("", "a"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaaa", "aa"),
        ("ab" * 50, "ba" * 50),
    ]
    rng = random.Random(42)
    for _ in range(20):
        alph = rng.choice(["ab", "abcd", "abcdefgh", "abcdefghijklmnopqrstuvwxyz"])
        la = rng.randint(0, 120)
        lb = rng.randint(0, 120)
        a = "".join(rng.choices(alph, k=la))
        b = "".join(rng.choices(alph, k=lb))
        cases.append((a, b))

    for a, b in cases:
        exp = dp_lcs(a, b)
        got = lcs.lcs_length(a, b)
        if got != exp:
            print(f"FAIL on len {len(a)},{len(b)}: got {got}, expected {exp}", file=sys.stderr)
            return False

    # Also verify CLI via subprocess on a 3000-char pair
    a3000 = "".join(rng.choices("ACGT", k=3000))
    b3000 = "".join(rng.choices("ACGT", k=3000))
    exp3000 = dp_lcs(a3000, b3000)
    res = subprocess.run(
        [sys.executable, "lcs.py"],
        input=f"{a3000}\n{b3000}\n",
         text=True,
        capture_output=True,
        timeout=10
    )
    if res.returncode != 0 or int(res.stdout.strip()) != exp3000:
        print(f"CLI FAIL: rc={res.returncode}, out={res.stdout!r}, exp={exp3000}", file=sys.stderr)
        return False

    return True

def benchmark():
    if not verify():
        print(0)
        sys.exit(1)

    rng = random.Random(12345)
    pairs = []
    # Mix of alphabets for 3000-char strings
    for alph in ["ACGT", "abcdefghij", "abcdefghijklmnopqrstuvwxyz0123456789", "01"]:
        for _ in range(25):
            a = "".join(rng.choices(alph, k=3000))
            b = "".join(rng.choices(alph, k=3000))
            pairs.append((a, b))

    # Warmup
    for a, b in pairs[:5]:
        lcs.lcs_length(a, b)

    t0 = time.perf_counter()
    iters = 0
    while time.perf_counter() - t0 < 0.8:
        for a, b in pairs:
            lcs.lcs_length(a, b)
        iters += len(pairs)
    elapsed = time.perf_counter() - t0
    # Score: pairs per second
    print(f"{iters / elapsed:.1f}")

if __name__ == "__main__":
    benchmark()
