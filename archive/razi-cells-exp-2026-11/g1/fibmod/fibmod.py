import sys

MOD = 1_000_000_007


def fib_mod(n: int) -> int:
    if n == 0:
        return 0
    a, b = 0, 1  # F(k), F(k+1), initially k=0
    for i in range(n.bit_length() - 1, -1, -1):
        c = a * ((b << 1) - a) % MOD          # F(2k)
        d = (a * a + b * b) % MOD             # F(2k+1)
        if (n >> i) & 1:
            a, b = d, (c + d) % MOD           # k -> 2k+1
        else:
            a, b = c, d                       # k -> 2k
    return a


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 fibmod.py <n>")
    print(fib_mod(int(sys.argv[1])))


if __name__ == "__main__":
    main()
