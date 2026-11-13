import sys
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    d = {}
    g = d.get
    for line in data[1:]:
        if not line:
            continue
        _, c, v = line.split(b',')
        if v[-3:-2] == b'.':
            n = int(v[:-3] + v[-2:])
        else:
            n = int(v.replace(b'.', b'')) if b'.' not in v else None
            if n is None:
                i = v.find(b'.')
                f = (v[i+1:] + b'00')[:2]
                n = int(v[:i] or b'0') * 100
                n = n - int(f) if v[:1] == b'-' else n + int(f)
            else:
                n *= 100
        d[c] = g(c, 0) + n
    out = []
    for c in sorted(d):
        s = d[c]
        sg = '-' if s < 0 else ''
        s = abs(s)
        out.append('%s,%s%d.%02d' % (c.decode(), sg, s // 100, s % 100))
    print('\n'.join(out))
main()
