import sys

MOD = 1_000_000_007

# Precompute base 2^16 tables
F0 = [0] * 65536
F0_next = [0] * 65536
a, b = 0, 1
for i in range(65536):
    F0[i] = a
    F0_next[i] = b
    a, b = b, (a + b) % MOD

# After loop, a = F_65536, b = F_65537
s_next = b
s_cur = a
s_prev = (b - a) % MOD

F1 = [0] * 30519
F1_prev = [0] * 30519
ca, cb = 0, 1
for i in range(30519):
    F1[i] = ca
    F1_prev[i] = cb
    ca, cb = (ca * s_next + cb * s_cur) % MOD, (ca * s_cur + cb * s_prev) % MOD

def fib(n, _F0=F0, _F0_next=F0_next, _F1=F1, _F1_prev=F1_prev):
    n %= 2_000_000_016
    n1 = n >> 16
    n0 = n & 0xFFFF
    return (_F1[n1] * _F0_next[n0] + _F1_prev[n1] * _F0[n0]) % 1_000_000_007

if __name__ == '__main__':
    print(fib(int(sys.argv[1])))
