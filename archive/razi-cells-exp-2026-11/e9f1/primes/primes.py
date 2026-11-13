import sys

try:
    from cprimes import count_primes
except ImportError:
    def count_primes(n):
        if n <= 2:
            return 0
        if n <= 5:
            return n - 2
        if n < 12000000:
            size = (n - 2) // 2
            sieve = bytearray(b'\x01') * size
            sieve[3::3] = bytearray((size - 4) // 3 + 1)
            limit = int((n - 1) ** 0.5)
            for i in range(1, (limit - 3) // 2 + 1):
                if sieve[i]:
                    p = 2 * i + 3
                    start = (p * p - 3) // 2
                    sieve[start::p] = bytearray((size - start - 1) // p + 1)
            return 1 + sieve.count(1)
        N = n - 1
        r = int(N ** 0.5)
        V = [N // i for i in range(1, r + 1)]
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
        return S[N] + 1

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
