import random
import subprocess
import sys
import time
import lcs

def ref_lcs(a: str, b: str) -> int:
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
    # Edge cases
    cases = [
        ("", ""),
        ("a", ""),
        ("", "b"),
        ("abc", "abc"),
        ("abc", "def"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaaa", "aa"),
        ("abcde", "ace"),
        ("x" * 100, "x" * 100),
    ]
    rng = random.Random(42)
    for alphabet in ["ab", "ACGT", "abcdefghijklmnopqrstuvwxyz", "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
        for _ in range(5):
            la = rng.randint(0, 120)
            lb = rng.randint(0, 120)
            sa = "".join(rng.choices(alphabet, k=la))
            sb = "".join(rng.choices(alphabet, k=lb))
            cases.append((sa, sb))

    # Check CLI subprocess on a couple cases
    for sa, sb in cases[:6]:
        p = subprocess.run([sys.executable, "lcs.py"], input=f"{sa}\n{sb}\n", text=True, capture_output=True)
        if p.returncode != 0:
            return False
        if int(p.stdout.strip()) != ref_lcs(sa, sb):
            return False

    # Check function or CLI on all cases
    for sa, sb in cases:
        expected = ref_lcs(sa, sb)
        # Call main via stdin/stdout replacement or lcs.lcs_length
        got = lcs.lcs_length(sa, sb)
        if got != expected:
            return False

    # Also verify one 3000-char pair via subprocess against known reference
    s1 = "".join(rng.choices("ACGT", k=3000))
    s2 = "".join(rng.choices("ACGT", k=3000))
    p = subprocess.run([sys.executable, "lcs.py"], input=f"{s1}\n{s2}\n", text=True, capture_output=True)
    if p.returncode != 0 or int(p.stdout.strip()) != lcs.lcs_length(s1, s2):
        return False
    # Check 600-char against ref_lcs
    if lcs.lcs_length(s1[:600], s2[:600]) != ref_lcs(s1[:600], s2[:600]):
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
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()",
        "ab",
    ]
    pairs = []
    for i in range(40):
        alph = alphabets[i % len(alphabets)]
        a = "".join(rng.choices(alph, k=3000))
        b = "".join(rng.choices(alph, k=3000))
        pairs.append((a, b))
    # Also include similar strings (common prefix/suffix)
    for i in range(10):
        base = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=3000))
        a = base[:1000] + "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=1000)) + base[2000:]
        b = base[:1000] + "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=1000)) + base[2000:]
        pairs.append((a, b))

    # Warmup
    for a, b in pairs[:5]:
        lcs.lcs_length(a, b)

    t0 = time.perf_counter()
    iters = 0
    while time.perf_counter() - t0 < 0.4:
        for a, b in pairs:
            lcs.lcs_length(a, b)
        iters += len(pairs)
    elapsed = time.perf_counter() - t0
    # Score: pairs per second
    print(f"{iters / elapsed:.1f}")

if __name__ == "__main__":
    benchmark()
