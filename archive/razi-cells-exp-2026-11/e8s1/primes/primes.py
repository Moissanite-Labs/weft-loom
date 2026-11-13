import sys
import math

# Odd-only Lucy-Hedgehog sublinear O(N^0.75) prime counting
def count_primes(n: int) -> int:
    n -= 1
    if n < 2:
        return 0
    if n == 2:
        return 1
    r = math.isqrt(n)
    # Small counts for 1..r: S0[i] = count of odd numbers in [1..i] = (i + 1) // 2
    # Large counts for n // k (k = 1..r): L0[k] = count of odd numbers in [1..n//k]
    S = [(i + 1) >> 1 for i in range(r + 1)]
    L = [0] + [((n // k) + 1) >> 1 for k in range(1, r + 1)]
    for p in range(3, r + 1, 2):
        if S[p] > S[p - 1]:
            sp = S[p - 1]
            p2 = p * p
            max_k = min(r, n // p2)
            # For k where k*p <= r, n // (k*p) is in L[k*p]
            mid_k = min(max_k, r // p)
            for k in range(1, mid_k + 1):
                L[k] -= L[k * p] - sp
            for k in range(mid_k + 1, max_k + 1):
                L[k] -= S[n // (k * p)] - sp
            for v in range(r, p2 - 1, -1):
                S[v] -= S[v // p] - sp
    return L[1]

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
