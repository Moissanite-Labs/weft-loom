import sys

MOD = 1_000_000_007
PISANO = 2_000_000_016

def _fast_fib(n: int) -> int:
    n %= PISANO
    if n == 0:
        return 0
    a, b = 0, 1
    for bit in range(n.bit_length() - 1, -1, -1):
        c = (a * ((b << 1) - a)) % MOD
        d = (a * a + b * b) % MOD
        if (n >> bit) & 1:
            a, b = d, (c + d) % MOD
        else:
            a, b = c, d
    return a

if __name__ == '__main__':
    print(_fast_fib(int(sys.argv[1])))
else:
    from _fibmod import fib
