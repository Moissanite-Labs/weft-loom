import sys

def count_primes(n):
    if n < 3:
        return 0
    # odd-only sieve: index i represents number 2*i+1
    size = n // 2  # covers odd numbers < n
    sieve = bytearray([1]) * size
    sieve[0] = 0  # 1 is not prime
    r = int(n ** 0.5)
    for i in range(1, r // 2 + 1):
        if sieve[i]:
            p = 2 * i + 1
            start = p * p // 2
            sieve[start::p] = bytes(len(range(start, size, p)))
    return 1 + sieve.count(1)

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
