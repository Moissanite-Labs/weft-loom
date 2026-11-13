import sys
from collections import defaultdict
def main():
    t = sys.stdin.buffer.read().replace(b"\r",b"").replace(b"\n",b",").split(b",")
    n=(len(t)-3)//3
    t=t[3:3+3*n]
    d = defaultdict(float)
    for k,v in zip(t[1::3],t[2::3]):
        d[k]+=float(v)
    print("\n".join(f"{k.decode()},{v:.2f}" for k,v in sorted(d.items())))
main()
