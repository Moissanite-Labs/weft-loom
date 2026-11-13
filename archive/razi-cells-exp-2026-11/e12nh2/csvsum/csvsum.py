import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    data = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    n = (len(data) - 3) // 3 * 3 + 3
    cats = data[4:n:3]
    vals = data[5:n:3]
    for c, v in zip(cats, vals):
        d[c] += float(v)
    out = ["%s,%.2f" % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write("\n".join(out) + "\n")
main()
