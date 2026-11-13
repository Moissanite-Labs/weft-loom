import sys
from math import isqrt
R = (1, 7, 11, 13, 17, 19, 23, 29)
INDEX = [0] * 30
for i, r in enumerate(R):
    INDEX[r] = i

def count_primes(n):
    if n <= 7:
        return int(n > 2) + int(n > 3) + int(n > 5)
    blocks, rem = divmod(n, 30)
    size = blocks * 8 + sum(r < rem for r in R)
    sieve = bytearray(b'\1') * size
    sieve[0] = 0
    limit = isqrt(n - 1)
    for i in range(1, limit // 30 * 8 + sum(r <= limit % 30 for r in R)):
        if sieve[i]:
            p = i // 8 * 30 + R[i % 8]
            step = 8 * p
            for r in R:
                x = p * (p + (r - p) % 30)
                start = x // 30 * 8 + INDEX[x % 30]
                sieve[start::step] = b'\0' * ((size - start - 1) // step + 1)
    return 3 + sieve.count(1)

if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
