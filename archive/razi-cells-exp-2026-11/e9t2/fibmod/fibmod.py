import sys

MOD = 1_000_000_007

class _Fib(dict):
    def __missing__(self, n):
        if n < 2:
            self[n] = n
            return n
        s = n.bit_length() - 1
        a, b = 1, 1
        for bit in bin(n)[3:]:
            c = a * ((b << 1) - a) % 1_000_000_007
            d = (a * a + b * b) % 1_000_000_007
            if bit == '1':
                a, b = d, (c + d) % 1_000_000_007
            else:
                a, b = c, d
        self[n] = a
        return a

fib = _Fib({0: 0, 1: 1, 2: 1}).__getitem__

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
