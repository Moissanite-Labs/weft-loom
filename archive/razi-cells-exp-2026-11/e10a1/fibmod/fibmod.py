import sys
def fib(n):
    q, k = divmod(n >> 1, 500000004)
    if k > 250000001:
        j = 500000003 - k
        rev = 1
    else:
        j = k
        rev = 0
    T = (2, 3, 7, 18, 47, 123, 322, 843, 2207, 5778, 15127, 39603, 103682, 271443, 710647, 1860498, 4870847)
    if j < 16:
        a = T[j]
        b = T[j + 1]
    else:
        t = j >> (j.bit_length() - 4)
        a = T[t]
        b = T[t + 1]
        for bit in bin(j)[6:]:
            c = (a * b - 3) % 1000000007
            if bit == '1':
                b = (b * b - 2) % 1000000007
                a = c
            else:
                a = (a * a - 2) % 1000000007
                b = c
    if n & 1:
        r = a + b
    elif rev:
        r = 2 * a - 3 * b
    else:
        r = 2 * b - 3 * a
    return r * (600000004 if (q ^ rev) & 1 else 400000003) % 1000000007
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
