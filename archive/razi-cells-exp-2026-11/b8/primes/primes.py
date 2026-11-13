import sys

def count_primes(n: int) -> int:
    if n <= 11:
        return (0, 0, 0, 1, 2, 2, 3, 3, 4, 4, 4, 4)[max(0, n)]
    n -= 1
    r = int(n ** 0.5)
    S0 = [((i + 1) // 6 + (i + 5) // 6) for i in range(r + 1)]
    S1 = [0] + [((n // i + 1) // 6 + (n // i + 5) // 6) for i in range(1, r + 1)]
    # Only iterate over i coprime to 6 in S1? No, S1[i] is needed for i coprime to 6!
    # Wait: if p >= 5 is prime (so coprime to 6), then i * p is only needed when i is coprime to 6!
    # Because we starts from i=1 and only multiply by primes >= 5!
    coprime_i = [i for i in range(1, r + 1) if i % 6 == 1 or i % 6 == 5]
    from bisect import bisect_right
    for p in range(5, r + 1, 2):
        if S0[p] > S0[p - 1]:
            sp = S0[p - 1]
            p2 = p * p
            max_i = min(r, n // p2)
            lim = r // p
            idx_lim = bisect_right(coprime_i, lim)
            idx_max = bisect_right(coprime_i, max_i)
            for i in coprime_i[:idx_lim]:
                S1[i] -= S1[i * p] - sp
            ni = n // p
            for i in coprime_i[idx_lim:idx_max]:
                S1[i] -= S0[ni // i] - sp
            for j in range(r, p2 - 1, -1):
                S0[j] -= S0[j // p] - sp
    return S1[1] + 1

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
