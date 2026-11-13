import sys
def main():
    d = sys.stdin.buffer.read().replace(b'.', b'').replace(b'\n', b',').split(b',')
    while d and d[-1] == b'': d.pop()
    cats = d[4::3]; vals = map(int, d[5::3])
    s = {}
    g = s.get
    for c, v in zip(cats, vals):
        s[c] = g(c, 0) + v
    out = []
    for c in sorted(s):
        v = s[c]; sg = '-' if v < 0 else ''; v = abs(v)
        out.append('%s,%s%d.%02d' % (c.decode(), sg, v // 100, v % 100))
    sys.stdout.write('\n'.join(out) + '\n')
main()
