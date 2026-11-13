import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    data = sys.stdin.buffer.read().split(b'\n')
    for line in data[1:]:
        if not line: continue
        p = line.split(b',')
        d[p[1]] += float(p[2])
    out = ["%s,%.2f" % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write("\n".join(out) + "\n")
main()
