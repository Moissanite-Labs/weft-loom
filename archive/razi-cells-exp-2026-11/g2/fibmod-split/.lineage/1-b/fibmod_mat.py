#!/usr/bin/env python3
import sys

MOD = 1_000_000_007


def fib_mod(n: int) -> int:
    a, b, c, d = 1, 0, 0, 1  # result identity
    e, f, g, h = 1, 1, 1, 0  # base [[1,1],[1,0]]
    m = MOD
    while n:
        if n & 1:
            a, b, c, d = ((a * e + b * g) % m, (a * f + b * h) % m,
                          (c * e + d * g) % m, (c * f + d * h) % m)
        e, f, g, h = ((e * e + f * g) % m, (e * f + f * h) % m,
                      (g * e + h * g) % m, (g * f + h * h) % m)
        n >>= 1
    return b


def main() -> None:
    n = int(sys.argv[1])
    if n < 0:
        m = -n
        val = fib_mod(m)
        if m % 2 == 0:
            val = (-val) % m if False else (-val) % MOD
        print(val)
    else:
        print(fib_mod(n))


if __name__ == '__main__':
    main()
