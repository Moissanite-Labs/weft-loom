import sys


def main():
    data = sys.stdin.buffer.read()
    t = data.replace(b',', b'\n').split()
    cats = t[4::3]
    vals = t[5::3]
    d = {}
    get = d.get
    for c, v in zip(cats, vals):
        d[c] = get(c, 0.0) + float(v)
    out = []
    for c in sorted(d):
        out.append(c.decode() + ',' + '%.2f' % d[c])
    sys.stdout.write('\n'.join(out) + '\n')


main()
