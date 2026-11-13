import subprocess
import sys
import time
import random
import lcs

def dp_lcs(a, b):
    dp = [0] * (len(b) + 1)
    for ca in a:
        prev = 0
        for j, cb in enumerate(b, 1):
            temp = dp[j]
            if ca == cb:
                dp[j] = prev + 1
            elif dp[j-1] > dp[j]:
                dp[j] = dp[j-1]
            prev = temp
    return dp[-1]

# 1. Verify correctness on edge cases and random strings
random.seed(42)
test_cases = [
    ("", ""),
    ("a", ""),
    ("", "a"),
    ("abc", "abc"),
    ("abc", "def"),
    ("AGGTAB", "GXTXAYB"),
    ("aaaaa", "aa"),
]
for _ in range(20):
    n = random.randint(1, 60)
    m = random.randint(1, 60)
    alphabet = random.choice(["ab", "abcd", "abcdefgh", "abcdefghijklmnopqrstuvwxyz"])
    s1 = "".join(random.choices(alphabet, k=n))
    s2 = "".join(random.choices(alphabet, k=m))
    test_cases.append((s1, s2))

for s1, s2 in test_cases:
    expected = dp_lcs(s1, s2)
    # Check via function if present, or subprocess
    if hasattr(lcs, 'lcs_length'):
        got = lcs.lcs_length(s1, s2)
        if got != expected:
            print(0)
            sys.exit(0)

# Also verify CLI execution on a couple cases including 3000-char strings
s3000_a = "".join(random.choices("ACGT", k=3000))
s3000_b = "".join(random.choices("ACGT", k=3000))
expected_3000 = dp_lcs(s3000_a, s3000_b)

proc = subprocess.run([sys.executable, "lcs.py"], input=f"{s3000_a}\n{s3000_b}\n", text=True, capture_output=True)
if proc.returncode != 0 or int(proc.stdout.strip()) != expected_3000:
    print(0)
    sys.exit(0)

# Generate benchmark pairs of 3000-char strings across various alphabet sizes
pairs = []
for alpha in ["01", "ACGT", "abcdefghij", "abcdefghijklmnopqrstuvwxyz0123456789"]:
    for _ in range(5):
        a = "".join(random.choices(alpha, k=3000))
        b = "".join(random.choices(alpha, k=3000))
        pairs.append((a, b))

# Warmup and check
if hasattr(lcs, 'lcs_length'):
    for a, b in pairs[:2]:
        lcs.lcs_length(a, b)

    t0 = time.perf_counter()
    iters = 0
    while time.perf_counter() - t0 < 0.6:
        for a, b in pairs:
            lcs.lcs_length(a, b)
        iters += len(pairs)
    elapsed = time.perf_counter() - t0
    print(f"{iters / elapsed:.2f}")
else:
    print(0)
