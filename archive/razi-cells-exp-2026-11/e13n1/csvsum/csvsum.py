import sys
def main():
    d = {}
    lines = sys.stdin.buffer.read().split(b'\n')
    for ln in lines[1:]:
        if not ln: continue
        p = ln.split(b',')
        k = p[1]
        v = round(float(p[2]) * 100)
        d[k] = d.get(k, 0) + v
    out = []
    for k in sorted(d):
        s = d[k]
        sg = '-' if s < 0 else ''
        s = abs(s)
        out.append('%s,%s%d.%02d' % (k.decode(), sg, s // 100, s % 100))
    print('\n'.join(out))
main()
