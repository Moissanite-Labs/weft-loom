import math
import sys

# Precompute tile of period 255255 (3 * 5 * 7 * 11 * 13 * 17) for odd numbers
_PERIOD = 255255
_TILE = bytearray(b'\x01') * _PERIOD
for _p in (3, 5, 7, 11, 13, 17):
    _TILE[_p >> 1 :: _p] = bytes(_PERIOD // _p)

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    if n <= 3:
        return 1
    size = n >> 1
    limit = (math.isqrt(n - 1) - 1) >> 1
    if size < 30:
        sieve = bytearray(b'\x01') * size
        sieve[0] = 0
        for i in range(1, limit + 1):
            if sieve[i]:
                p = (i << 1) | 1
                start = (p * p) >> 1
                sieve[start::p] = bytes((size - 1 - start) // p + 1)
        return sieve.count(1) + 1

    if size <= _PERIOD:
        sieve = _TILE[:size]
    else:
        sieve = _TILE * (size // _PERIOD) + _TILE[: size % _PERIOD]
    sieve[0] = 0
    sieve[1] = 1
    sieve[2] = 1
    sieve[3] = 1
    sieve[5] = 1
    sieve[6] = 1
    sieve[8] = 1

    for i in range(9, limit + 1):
        if sieve[i]:
            p = (i << 1) | 1
            start = (p * p) >> 1
            sieve[start::p] = bytes((size - 1 - start) // p + 1)
    return sieve.count(1) + 1

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
