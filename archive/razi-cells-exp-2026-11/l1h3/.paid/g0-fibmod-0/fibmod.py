import sys
M = 1000000007

def mm(A, B):
    return ((A[0]*B[0] + A[1]*B[2]) % M, (A[0]*B[1] + A[1]*B[3]) % M,
            (A[2]*B[0] + A[3]*B[2]) % M, (A[2]*B[1] + A[3]*B[3]) % M)

# T[i][v] = M^(v * 256^i), where M = [[1,1],[1,0]]; 8 byte-chunks cover n < 2^64
T = []
base = (1, 1, 1, 0)
I = (1, 0, 0, 1)
for i in range(8):
    row = [I]
    for v in range(1, 256):
        row.append(mm(row[-1], base))
    T.append(row)
    base = mm(row[255], base)

def fib(n):
    v0, v1 = 1, 0
    i = 0
    while n:
        c = n & 255
        if c:
            t = T[i][c]
            v0, v1 = (v0*t[0] + v1*t[2]) % M, (v0*t[1] + v1*t[3]) % M
        n >>= 8
        i += 1
    return v1

def main():
    out = [str(fib(int(x))) for x in sys.stdin.read().split()]
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

main()
