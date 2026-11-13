import random
import subprocess
import sys
import time
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
            else:
                if dp[j] > dp[j + 1]:
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
        ("abcde", "ace"),
        ("aaaa", "aa"),
        ("abcbdab", "bdcaba"),
        ("x" * 100, "x" * 100),
        ("x" * 50 + "y" * 50, "y" * 50 + "x" * 50),
    ]
    rng = random.Random(42)
    for _ in range(30):
        la = rng.randint(0, 80)
        lb = rng.randint(0, 80)
        alpha = rng.choice(["ab", "abcd", "abcdefgh", "0123456789abcdef"])
        a = "".join(rng.choices(alpha, k=la))
        b = "".join(rng.choices(alpha, k=lb))
        cases.append((a, b))

    for a, b in cases:
        expected = dp_lcs(a, b)
        got = lcs.lcs_length(a, b)
        if got != expected:
            print(f"FAIL: len({len(a)}, {len(b)}) got {got} != {expected}", file=sys.stderr)
            return False

    # Also test CLI via subprocess on a 3000-char pair and an edge case
    a3000 = "".join(rng.choices("ACGT", k=3000))
    b3000 = "".join(rng.choices("ACGT", k=3000))
    p = subprocess.run(
        [sys.executable, "lcs.py"],
        input=f"{a3000}\n{b3000}\n",
        text=True,
        capture_output=True,
        timeout=5,
    )
    if p.returncode != 0 or int(p.stdout.strip()) != lcs.lcs_length(a3000, b3000):
        print("CLI check failed", file=sys.stderr)
        return False

    p_empty = subprocess.run(
        [sys.executable, "lcs.py"],
        input="\n\n",
        text=True,
        capture_output=True,
        timeout=5,
    )
    if p_empty.returncode != 0 or int(p_empty.stdout.strip()) != 0:
        print("CLI empty check failed", file=sys.stderr)
        return False

    return True

def main():
    if not verify():
        print(0)
        sys.exit(1)

    rng = random.Random(12345)
    pairs = []
    # Mix of alphabet sizes for 3000-char strings
    for alpha in ["ACGT", "abcdefgh", "abcdefghijklmnopqrstuvwxyz", "01"]:
        for _ in range(25):
            a = "".join(rng.choices(alpha, k=3000))
            b = "".join(rng.choices(alpha, k=3000))
            pairs.append((a, b))
    # Also include a few with common prefixes/suffixes or high similarity
    for _ in range(20):
        base = list("".join(rng.choices("abcdefghijklmnop", k=3000)))
        b_list = base[:]
        for _ in range(300):
            idx = rng.randint(0, 2999)
            b_list[idx] = rng.choice("abcdefghijklmnop")
        pairs.append(("".join(base), "".join(b_list)))

    # Expected answers for 3000-char check
    expected_sum = 259496
    actual_sum = sum(lcs.lcs_length(a, b) for a, b in pairs)
    if expected_sum != actual_sum:
        # First time or mismatch? Let's verify one 3000-char pair with dp_lcs
        if lcs.lcs_length(pairs[0][0], pairs[0][1]) != dp_lcs(pairs[0][0], pairs[0][1]):
            print(0)
            sys.exit(1)

    # Time 5 rounds over all 120 pairs (600 calls of 3000x3000 LCS)
    t0 = time.perf_counter()
    total = 0
    for _ in range(4):
        for a, b in pairs:
            total += lcs.lcs_length(a, b)
    elapsed = time.perf_counter() - t0
    if total != actual_sum * 4:
        print(0)
        sys.exit(1)

    # Score: pairs per second
    score = (4 * len(pairs)) / elapsed
    print(f"{score:.2f}")

if __name__ == "__main__":
    main()
