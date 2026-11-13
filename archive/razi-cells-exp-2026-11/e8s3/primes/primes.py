import sys
import numpy as np

def count_primes(n: int) -> int:
    if n <= 2:
        return 0
    sieve = np.ones(n // 2, dtype=bool)
    for i in range(3, int(n**0.5) + 1, 2):
        if sieve[i // 2]:
            sieve[i * i // 2 :: i] = False
    return int(np.count_nonzero(sieve))

if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
