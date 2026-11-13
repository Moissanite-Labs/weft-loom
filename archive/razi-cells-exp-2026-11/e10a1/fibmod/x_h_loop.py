import sys
def fib(n):
    q, k = divmod(n >> 1, 500000004)
    if k > 250000001:
        j = 500000003 - k
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
        r = a + b
    elif rev:
        r = 2 * a - 3 * b
    else:
        r = 2 * b - 3 * a
    return r * (600000004 if (q ^ rev) & 1 else 400000003) % 1000000007
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
