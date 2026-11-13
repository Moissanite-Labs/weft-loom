import sys

def count_primes(n):
    if n < 3:
        return 0
    size = n // 2
    sieve = bytearray([1]) * size
    sieve[0] = 0
    r = int(n ** 0.5)
    zeros = memoryview(bytes((size // 3) + 2))
    # small primes handled with sieve-of-small-prime pattern multiplication
    for i in range(1, r // 2 + 1):
        if sieve[i]:
            p = 2 * i + 1
            start = p * p // 2
            cnt = (size - start + p - 1) // p
            if cnt > 0:
                sieve[start::p] = zeros[:cnt]
    return 1 + sieve.count(1)

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
