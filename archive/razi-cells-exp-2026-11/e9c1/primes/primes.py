import sys

def count_primes(n):
    if n <= 2:
        return 0
    if n <= 3:
        return 1
    if n <= 5:
        return 2
    n -= 1
    # Meissel-Lehmer / Lucy DP O(n^(3/4)) with odd numbers only
    r = int(n ** 0.5)
    # For small n, simple sieve is faster
    if n < 10000:
        size = (n + 1) // 2
        sieve = bytearray(b'\x01') * size
        sieve[0] = 0
        for i in range(1, r // 2 + 1):
            if sieve[i]:
                p = 2 * i + 1
                start = (p * p) // 2
                sieve[start::p] = b'\x00' * ((size - start - 1) // p + 1)
        return sieve.count(1) + 1

    # Sieve up to y = int(n ** 0.66)
    y = int(n ** 0.65)
    if y < r:
        y = r
    size = y // 2 + 1
    sieve = bytearray(b'\x01') * size
    sieve[0] = 0
    for i in range(1, int(y ** 0.5) // 2 + 1):
        if sieve[i]:
            p = 2 * i + 1
            start = (p * p) // 2
            sieve[start::p] = b'\x00' * ((size - start - 1) // p + 1)

    # pi table up to y
    # Wait: let's use simple odd Lucy DP for testing speed
    V = [n // i for i in range(1, r + 1)]
    V += list(range(V[-1] - 1, 0, -1))
    S = {v: (v - 1) // 2 for v in V}
    for p in range(3, r + 1, 2):
        if S[p] > S[p - 1]:
            sp = S[p - 1]
            p2 = p * p
            for v in V:
                if v < p2:
                    break
                S[v] -= S[v // p] - sp
    return S[n] + 1

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
