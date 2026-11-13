import sys
def fib(n):
    k = (n >> 1) % 1000000008
    if k > 500000003:
        j = 1000000007 - k
        rev = 1
    else:
        j = k
        rev = 0
    if j:
        a, b = 3, 7
        for bit in bin(j)[3:]:
            if bit == '1':
                a, b = (a * b - 3) % 1000000007, (b * b - 2) % 1000000007
            else:
                a, b = (a * a - 2) % 1000000007, (a * b - 3) % 1000000007
    else:
        a, b = 2, 3
    if n & 1:
        return (a + b) * 400000003 % 1000000007
    if rev:
        return (2 * a - 3 * b) * 400000003 % 1000000007
    return (2 * b - 3 * a) * 400000003 % 1000000007
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
