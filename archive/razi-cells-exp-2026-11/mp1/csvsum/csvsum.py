import sys

def main():
    t = sys.stdin.buffer.read().replace(b',', b' ').split()
    cats = t[4::3]
    vals = t[5::3]
    d = {}
    get = d.get
    for c, v in zip(cats, map(float, vals)):
        d[c] = get(c, 0.0) + v
    out = []
    for c in sorted(d):
        out.append(c.decode() + ',' + '%.2f' % d[c])
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))

main()
