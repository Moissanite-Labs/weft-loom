import sys
from collections import defaultdict
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    d = defaultdict(float)
    for line in data[1:]:
        if line:
            _, c, v = line.split(b',')
            d[c] += float(v)
    out = ['%s,%.2f\n' % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write(''.join(out))
main()
