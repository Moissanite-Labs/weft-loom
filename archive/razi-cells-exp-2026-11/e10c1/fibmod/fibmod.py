import sys
M = 1000000007
P = 2000000016  # Pisano period divides 2(p+1) since p = 2 mod 5
S = 1 << 16
# L[i] = F(i) for i in 0..S
L = [0] * (S + 1)
a, b = 0, 1
for i in range(S + 1):
    L[i] = a
    a, b = b, (a + b) % M
fS, fS1 = L[S], a  # F(S), F(S+1)
fSm1 = L[S - 1]
H = P // S + 2
A = [0] * H  # F(h*S)
B = [0] * H  # F(h*S - 1)
x, y = 0, 1  # F(m), F(m+1) with m = h*S
for h in range(H):
    A[h] = x
    B[h] = (y - x) % M
    x, y = (fS * y + fSm1 * x) % M, (fS1 * y + fS * x) % M

def fib(n, A=A, B=B, L=L, M=M, P=P):
    n %= P
    h = n >> 16
    l = n & 65535
    return (A[h] * L[l + 1] + B[h] * L[l]) % M

if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
