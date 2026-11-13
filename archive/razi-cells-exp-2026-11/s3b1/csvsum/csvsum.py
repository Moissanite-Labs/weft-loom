import sys
def main():
    t = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    if t and t[-1] == b'': t.pop()
    cats = t[4::3]
    vals = map(float, t[5::3])
    d = {}
    g = d.get
    for c, v in zip(cats, vals):
        d[c] = g(c, 0.0) + v
    out = ['%s,%.2f' % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write('\n'.join(out) + '\n')
main()
