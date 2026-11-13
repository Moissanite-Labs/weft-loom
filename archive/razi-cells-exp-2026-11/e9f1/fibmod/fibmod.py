import sys

# Precompute small Fibonacci numbers (12-bit base = up to 4095)
_F = [0, 1]
_a, _b = 0, 1
for _ in range(4096):
    _a, _b = _b, (_a + _b) % 1_000_000_007
    _F.append(_b)

class _Fib(dict):
    def __missing__(self, orig_n):
        n = orig_n % 2_000_000_016
        if n <= 4096:
            res = _F[n]
            self[orig_n] = res
            return res
        bl = n.bit_length()
        top = bl - 12
        idx = n >> top
        a, b = _F[idx], _F[idx + 1]
        for i in range(top - 1, 0, -1):
            c = a * ((b << 1) - a) % 1_000_000_007
            d = (a * a + b * b) % 1_000_000_007
            if (n >> i) & 1:
                a, b = d, (c + d) % 1_000_000_007
            else:
                a, b = c, d
        if n & 1:
            res = (a * a + b * b) % 1_000_000_007
        else:
            res = a * ((b << 1) - a) % 1_000_000_007
        self[orig_n] = res
        return res

fib = _Fib().__getitem__

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
