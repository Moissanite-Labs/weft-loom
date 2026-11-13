#!/usr/bin/env python3
import sys

MOD = 1_000_000_007


def fib_mod(n: int) -> int:
    """Return F(n) mod MOD using iterative fast doubling."""
    a, b = 0, 1
    for ch in bin(n)[2:]:
        c = (a * ((b << 1) - a)) % MOD
        d = (a * a + b * b) % MOD
        if ch == '0':
            a, b = c, d
        else:
            a, b = d, (c + d) % MOD
    return a


def main() -> None:
    n = int(sys.argv[1])
    if n < 0:
        m = -n
        val = fib_mod(m)
        if m % 2 == 0:
            val = (-val) % MOD
        print(val)
    else:
        print(fib_mod(n))


if __name__ == '__main__':
    main()
