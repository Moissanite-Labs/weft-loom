import sys
from collections import defaultdict
def main():
    data = sys.stdin.buffer.read().replace(b"\r", b"")
    i = data.find(b"\n")
    t = data[i+1:].replace(b"\n", b",").split(b",")
    n = len(t) // 3 * 3
    d = defaultdict(float)
    for c, v in zip(t[1:n:3], map(float, t[2:n:3])):
        d[c] += v
    out = ["%s %.2f" % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))
main()
