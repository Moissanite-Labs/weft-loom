import sys


def count_primes(n):
    """Count primes p with p < n (odd-only bytearray sieve)."""
    if n <= 2:
        return 0
    if n == 3:
        return 1
    # index i represents odd number 2*i+1; numbers < n
    half = n // 2  # odds 1,3,...,(2*half-1) < n
    sieve = bytearray([1]) * half
    sieve[0] = 0  # 1 is not prime
    i = 1
    while True:
        p = 2 * i + 1
        if p * p >= n:
            break
        if sieve[i]:
            start = (p * p) // 2
            sieve[start::p] = bytes(len(range(start, half, p)))
        i += 1
    return sieve.count(1) + 1  # +1 for the prime 2


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
