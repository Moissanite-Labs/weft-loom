MOD = 1000000007
PER = 2000000016

def fd(n):
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * ((b + b - a) % MOD) % MOD
        d = (a * a + b * b) % MOD
        if bit == '0': a, b = c, d
        else: a, b = d, (c + d) % MOD
    return a, b

BITS = 11
BASE = 1 << BITS  # 2048

def build(shift):
    s = 1 << shift
    a, b = fd(s)          # F(s), F(s+1)
    cnt = (1 << 31) >> shift
    if cnt > BASE: cnt = BASE
    tab = [(0, 1)]
    x, y = 0, 1
    for k in range(1, cnt):
        # combine (x,y)=F(x),F(x+1) with (a,b)=F(s),F(s+1)
        x, y = (y * a + x * (b - a)) % MOD, (y * b + x * a) % MOD
        tab.append((x, y))
    return tab

tabs = [build(BITS * j) for j in range(3)]
print("sizes", [len(t) for t in tabs])

parts = []
parts.append("import sys\n\nMOD = 1000000007\nPER = 2000000016\n")
for j, t in enumerate(tabs):
    parts.append("A%d = %r\n" % (j, tuple(t)))
parts.append('''
def fib(n):
    n %= PER
    a, b = A0[n & 2047]
    c, d = A1[(n >> 11) & 2047]
    a, b = (b * c + a * (d - c)) % MOD, (b * d + a * c) % MOD
    c, d = A2[n >> 22]
    return (b * c + a * (d - c)) % MOD


def main():
    sys.stdout.write(str(fib(int(sys.argv[1]))) + "\\n")


if __name__ == "__main__":
    main()
''')
open("fibmod.py", "w").write("".join(parts))
import os
print("size", os.path.getsize("fibmod.py"))
