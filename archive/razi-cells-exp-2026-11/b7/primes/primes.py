import sys

try:
    import sieve
except ImportError:
    sieve = None

def count(n):
    if sieve is not None:
        return sieve.count(n)
    if n <= 2:
        return 0
    import math
    m = (n - 2) // 2
    a = bytearray(b'\x01') * m
    lim = math.isqrt(n - 1)
    for j in range((lim - 3) // 2 + 1):
        if a[j]:
            p = 2 * j + 3
            start = (p * p - 3) // 2
            a[start::p] = b'\x00' * (((m - 1 - start) // p) + 1)
    return 1 + sum(a)

if __name__ == '__main__':
    print(count(int(sys.argv[1])))
