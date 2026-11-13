import sys, math

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    if n <= 3:
        return 1
    if n <= 5:
        return 2
    s0 = (n + 4) // 6
    s1 = n // 6
    sieve0 = bytearray([1]) * s0
    sieve1 = bytearray([1]) * s1
    sieve0[0] = 0
    limit = math.isqrt(n - 1)
    k_limit = limit // 6 + 1
    for k in range(k_limit):
        if k < s0 and sieve0[k]:
            p = 6 * k + 1
            start0 = (p * p) // 6
            if start0 < s0:
                sieve0[start0::p] = bytes((s0 - start0 - 1) // p + 1)
            start1 = (p * p + 4 * p) // 6
            if start1 < s1:
                sieve1[start1::p] = bytes((s1 - start1 - 1) // p + 1)
        if k < s1 and sieve1[k]:
            p = 6 * k + 5
            start0 = (p * p) // 6
            if start0 < s0:
                sieve0[start0::p] = bytes((s0 - start0 - 1) // p + 1)
            start1 = (p * p + 2 * p) // 6
            if start1 < s1:
                sieve1[start1::p] = bytes((s1 - start1 - 1) // p + 1)
    return sieve0.count(1) + sieve1.count(1) + 2

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
