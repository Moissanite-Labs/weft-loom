import sys

MOD = 1_000_000_007
# Pisano period of Fibonacci numbers modulo 1_000_000_007 (prime, p % 5 == 2)
# equals 2*(p+1) = 2000000016.  Verified numerically.
PERIOD = 2000000016


def fib(n, mod=MOD):
    """F(n) mod mod via fast doubling, iterating over bits of n (MSB first)."""
    n %= PERIOD
    a, b = 0, 1  # F(0), F(1)
    for ch in bin(n)[2:]:
        c = a * ((2 * b - a) % mod) % mod   # F(2k)
        d = (a * a + b * b) % mod           # F(2k+1)
        if ch == '0':
            a, b = c, d
        else:
            a, b = d, (c + d) % mod
    return a


if __name__ == '__main__':
    print(fib(int(sys.argv[1])))
