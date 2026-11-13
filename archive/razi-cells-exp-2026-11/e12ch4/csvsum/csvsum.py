import sys
from collections import defaultdict
def main():
    data = sys.stdin.buffer.read().split(b"\n")
    d = defaultdict(float)
    for line in data[1:]:
        p = line.split(b",")
        if len(p) < 3: continue
        d[p[1]] += float(p[2])
    print("\n".join("%s %.2f" % (k.decode(), d[k]) for k in sorted(d)))
main()
