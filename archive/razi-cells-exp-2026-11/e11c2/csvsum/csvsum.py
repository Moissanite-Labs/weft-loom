import sys
from collections import defaultdict
def main():
    t = sys.stdin.buffer.read().replace(b"\r", b"").strip().replace(b"\n", b",")
    f = t.split(b",")
    d = defaultdict(float)
    for c, v in zip(f[4::3], map(float, f[5::3])):
        d[c] += v
    print("\n".join("%s %.2f" % (k.decode(), d[k]) for k in sorted(d)))
main()
