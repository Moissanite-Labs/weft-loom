import sys
M = 1_000_000_007
P = 2_000_000_016  # Pisano period divides 2(M+1) since 5 is a non-residue mod M

def _fib_fd(n, M=M):
    # fast doubling on n mod P (<2^31 -> ~31 steps); used by the CLI to avoid table build
    n %= P
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (2 * b - a) % M
        d = (a * a + b * b) % M
        if bit == '1':
            a, b = d, (c + d) % M
        else:
            a, b = c, d
    return a

if __name__ == "__main__":
    print(_fib_fd(int(sys.argv[1])))
else:
    def _build(L, sa, sb):
        A = [0] * L; D = [0] * L
        a, b = 0, 1
        for i in range(L):
            A[i] = a; D[i] = (b - a) % M
            a, b = (a * sb + (b - a) * sa) % M, (b * sb + a * sa) % M
        return A, D, a, b

    A0, D0, s1a, s1b = _build(1 << 18, 1, 1)
    A1, D1, _, _ = _build(1 << 13, s1a, s1b)
    B1 = [(a + d) % M for a, d in zip(A1, D1)]

    def fib(n, P=P, A0=A0, D0=D0, A1=A1, B1=B1, M=M):
        # O(1): n mod Pisano period, then F(i+j*2^18) via addition formula on precomputed tables
        n %= P
        i = n & 262143
        j = n >> 18
        return (A0[i] * B1[j] + D0[i] * A1[j]) % M
