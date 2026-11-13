import sys
from collections import defaultdict
def main():
    t = sys.stdin.buffer.read().replace(b"\r",b"").replace(b"\n", b",").split(b",")
    d = defaultdict(float)
    for k, v in zip(t[4::3], t[5::3]):
        d[k] += float(v)
    print("\n".join("%s %.2f" % (k.decode(), d[k]) for k in sorted(d)))
main()
