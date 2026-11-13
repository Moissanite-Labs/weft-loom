import sys

def count_primes(n):
    if n < 3:
        return 0
    size = n // 2  # index i <-> odd number 2*i+1
    small = [3, 5, 7, 11, 13, 17, 19]
    M = 1
    for p in small:
        M *= p
    if size <= 2 * M:
        sieve = bytearray([1]) * size
        sieve[0] = 0
        r = int(n ** 0.5)
        for i in range(1, r // 2 + 1):
            if sieve[i]:
                p = 2 * i + 1
                start = p * p // 2
                sieve[start::p] = bytes(len(range(start, size, p)))
        return 1 + sieve.count(1)
    # build periodic pattern for small primes (period M in odd-index space)
    pat = bytearray([1]) * M
    for p in small:
        pat[p // 2::p] = bytes(len(range(p // 2, M, p)))
    sieve = pat * (size // M + 1)
    del sieve[size:]
    sieve[0] = 0
    for p in small:
        sieve[p // 2] = 1
    r = int(n ** 0.5)
    for i in range(11, r // 2 + 1):  # start at 23
        if sieve[i]:
            p = 2 * i + 1
            start = p * p // 2
            sieve[start::p] = bytes(len(range(start, size, p)))
    return 1 + sieve.count(1)

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
