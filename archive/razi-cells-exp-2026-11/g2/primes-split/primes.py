import sys


def count_primes(n):
    """Number of primes strictly below n (odd-only bytearray sieve)."""
    if n < 3:
        return 0
    size = n // 2  # indices i -> 2*i+1, odd numbers below n
    sieve = bytearray(b'\x01') * size
    sieve[0] = 0  # 1 is not prime
    i = 1
    while True:
        p = 2 * i + 1
        if p * p >= n:
            break
        if sieve[i]:
            start = 2 * i * (i + 1)  # index of p*p
            step = p
            sieve[start::step] = b'\x00' * (((size - 1 - start) // step) + 1)
        i += 1
    return 1 + sieve.count(1)


def main():
    print(count_primes(int(sys.argv[1])))


main()
