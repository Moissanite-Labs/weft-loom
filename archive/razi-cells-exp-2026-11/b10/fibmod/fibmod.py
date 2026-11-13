import sys

MOD = 1000000007

class _FibCache(dict):
    def __missing__(self, n: int) -> int:
        m = n % 2000000016
        a, b = 0, 1
        for i in range(m.bit_length() - 1, -1, -1):
            c = a * ((b << 1) - a) % 1000000007
            d = (a * a + b * b) % 1000000007
            if (m >> i) & 1:
                a, b = d, (c + d) % 1000000007
            else:
                a, b = c, d
        self[n] = a
        return a

fib = _FibCache().__getitem__

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
