import sys

MOD = 1000000007
PER = 2000000016  # Pisano period of 1e9+7 (5 is a non-residue mod p)
L = 15
S = 1 << L
MASK = S - 1


def _fb(n):
    """(F(n), F(n+1)) mod MOD by iterative fast doubling."""
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (b + b - a) % MOD
        d = (a * a + b * b) % MOD
        if bit == '0':
            a, b = c, d
        else:
            a, b = d, (c + d) % MOD
    return a, b


_A0 = None


def _tables():
    """A0[r]=F(r), A1[r]=F(r+1) for r < 2^L;
    B0[q]=F(q*2^L), B1[q]=F(q*2^L - 1) covering q*2^L <= PER."""
    global _A0
    a0 = [0] * S
    a1 = [1] * S
    x, y = 0, 1
    for i in range(1, S):
        x, y = y, x + y
        if y >= MOD:
            y -= MOD
        a0[i] = x
        a1[i] = y
    fs, fs1 = _fb(S)          # F(S), F(S+1)
    fsm1 = (fs1 - fs) % MOD   # F(S-1)
    nb = ((PER - 1) >> L) + 2
    b0 = [0] * nb
    b1 = [0] * nb
    p, q = 0, 1               # F(0), F(1)
    for k in range(nb):
        b0[k] = p
        b1[k] = (q - p) % MOD
        p, q = (p * fsm1 + q * fs) % MOD, (p * fs + q * fs1) % MOD
    _A0 = (a0, a1, b0, b1)
    return _A0


def fib(n):
    t = _A0 or _tables()
    a0, a1, b0, b1 = t
    n %= PER
    r = n & MASK
    q = n >> L
    return (a1[r] * b0[q] + a0[r] * b1[q]) % MOD


def main():
    sys.stdout.write(str(fib(int(sys.argv[1]))) + "\n")


if __name__ == "__main__":
    main()
