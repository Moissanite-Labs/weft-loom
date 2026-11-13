import sys
from collections import defaultdict
def main():
    t = sys.stdin.buffer.read().replace(b'\r', b'').strip().replace(b'\n', b',').split(b',')
    cats = t[4::3]
    vals = map(float, t[5::3])
    d = defaultdict(float)
    for c, v in zip(cats, vals):
        d[c] += v
    sys.stdout.write(''.join('%s,%.2f\n' % (k.decode(), d[k]) for k in sorted(d)))
main()
