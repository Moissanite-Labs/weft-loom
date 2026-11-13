import sys

MOD = 1_000_000_007
PISANO = 2_000_000_016

if __name__ == '__main__':
    n = int(sys.argv[1]) % 2_000_000_016
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((b << 1) - a) % 1_000_000_007
        d = (a * a + b * b) % 1_000_000_007
        if bit == '1':
            a, b = d, (c + d) % 1_000_000_007
        else:
            a, b = c, d
    print(a)
    sys.exit(0)

def _make_fib():
    mod = 1_000_000_007
    L0 = [0] * 32768
    L1 = [0] * 32768
    a, b = 1, 0
    for m in range(32768):
        L0[m] = a
        L1[m] = b
        a, b = b, (a + b) % mod
    s_prev, s_curr, s_next = a, b, (a + b) % mod
    H0 = [0] * 61036
    H1 = [0] * 61036
    ha, hb = 0, 1
    for k in range(61036):
        H0[k] = ha
        H1[k] = hb
        ha, hb = (ha * s_prev + hb * s_curr) % mod, (ha * s_curr + hb * s_next) % mod

    class _FibCache(dict):
        def __missing__(self, n):
            m = n % 2_000_000_016
            hi = m >> 15
            lo = m & 0x7FFF
            res = (H0[hi] * L0[lo] + H1[hi] * L1[lo]) % 1_000_000_007
            self[n] = res
            return res

    return _FibCache().__getitem__

fib = _make_fib()
