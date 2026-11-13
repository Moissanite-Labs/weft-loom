    n %= 2000000016
    c5 = 400000003
    m = n >> 1
    if m < 1024:
        a = _W[m]; b = _W[m + 1]
    else:
        k = m >> (m.bit_length() - 10)
        a = _W[k]; b = _W[k + 1]
        for c in bin(m)[12:]:
            if c == '1':
                a, b = (a * b - 3) % 1000000007, (b * b - 2) % 1000000007
            else:
                a, b = (a * a - 2) % 1000000007, (a * b - 3) % 1000000007
    if n & 1:
        return (a + b) * c5 % 1000000007
    return (2 * b - 3 * a) * c5 % 1000000007
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
