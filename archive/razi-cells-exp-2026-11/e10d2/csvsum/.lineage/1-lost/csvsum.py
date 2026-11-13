import sys
from collections import defaultdict

def main():
    data = sys.stdin.buffer.read().decode('ascii', 'replace')
    lines = data.split('\n')
    # drop header
    start = 1 if lines and lines[0].startswith('id,') else 0
    sums = defaultdict(float)
    for ln in lines[start:]:
        if not ln:
            continue
        _, c, v = ln.split(',', 2)
        sums[c] += float(v)
    out = []
    for c in sorted(sums):
        out.append("%s,%.2f" % (c, sums[c]))
    sys.stdout.write("\n".join(out) + "\n")

main()
