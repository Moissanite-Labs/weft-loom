import subprocess
import sys
import time
import random
import lcs

def naive_lcs(a, b):
    dp = [0] * (len(b) + 1)
    for ch_a in a:
        prev = 0
        for j, ch_b in enumerate(b):
            temp = dp[j + 1]
            if ch_a == ch_b:
                dp[j + 1] = prev + 1
            else:
                if dp[j] > dp[j + 1]:
                    dp[j + 1] = dp[j]
            prev = temp
    return dp[-1]

def ref_bit_lcs(a, b):
    if len(a) > len(b):
        a, b = b, a
    if not a:
        return 0
    masks = {}
    for i, ch in enumerate(a):
        masks[ch] = masks.get(ch, 0) | (1 << i)
    S = (1 << len(a)) - 1
    for ch in b:
        pm = masks.get(ch, 0)
        u = S & pm
        S = (S + u) | (S - u)
    return len(a) - (S & ((1 << len(a)) - 1)).bit_count()

def run_lcs_subproc(a, b):
    inp = f"{a}\n{b}\n"
    res = subprocess.run([sys.executable, "lcs.py"], input=inp, text=True, capture_output=True)
    if res.returncode != 0:
        return -1
    try:
        return int(res.stdout.strip())
    except:
        return -1

rng = random.Random(42)
test_cases = [
    ("", ""),
    ("a", ""),
    ("", "b"),
    ("abc", "abc"),
    ("abc", "def"),
    ("AGGTAB", "GXTXAYB"),
    ("aaaa", "aa"),
    ("ab" * 150, "ba" * 150),
]
for alphabet in ["ab", "abcd", "abcdefghijklmnopqrstuvwxyz0123456789"]:
    for _ in range(3):
        la = rng.randint(1, 80)
        lb = rng.randint(1, 80)
        sa = "".join(rng.choices(alphabet, k=la))
        sb = "".join(rng.choices(alphabet, k=lb))
        test_cases.append((sa, sb))

for a, b in test_cases:
    expected = naive_lcs(a, b)
    if lcs.lcs_length(a, b) != expected:
        print(0)
        sys.exit(0)

# Verify subprocess on a few cases including 3000-char
sa3000 = "".join(rng.choices("abcd", k=3000))
sb3000 = "".join(rng.choices("abcd", k=3000))
exp3000 = ref_bit_lcs(sa3000, sb3000)
if run_lcs_subproc("AGGTAB", "GXTXAYB") != 4 or run_lcs_subproc(sa3000, sb3000) != exp3000:
    print(0)
    sys.exit(0)

# Prepare benchmark dataset: 200 pairs of 3000-char strings across various alphabets and lengths
bench_pairs = []
alphabets = [
    "ab",
    "ACGT",
    "abcdefgh",
    "abcdefghijklmnopqrstuvwxyz",
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
]
for i in range(200):
    alph = alphabets[i % len(alphabets)]
    a = "".join(rng.choices(alph, k=3000))
    b = "".join(rng.choices(alph, k=3000))
    # Include some with shared prefixes/suffixes or identical blocks
    if i % 10 == 0:
        a = a[:500] + b[500:2500] + a[2500:]
    bench_pairs.append((a, b, ref_bit_lcs(a, b)))

t0 = time.perf_counter()
for a, b, exp in bench_pairs:
    ans = lcs.lcs_length(a, b)
    if ans != exp:
        print(0)
        sys.exit(0)
elapsed = time.perf_counter() - t0

# Score: pairs per second
print(f"{len(bench_pairs) / elapsed:.2f}")
