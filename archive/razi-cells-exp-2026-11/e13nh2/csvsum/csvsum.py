import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    d = {}
    g = d.get
    for line in data[1:]:
        if not line:
            continue
        a = line.split(b',')
        c = a[1]
        v = a[2].strip()
        # integer cents
        i = v.find(b'.')
        if i < 0:
            n = int(v) * 100
        else:
            f = (v[i+1:] + b'00')[:2]
            ip = v[:i]
            neg = ip.startswith(b'-')
            n = abs(int(ip or b'0')) * 100 + int(f)
            if neg:
                n = -n
        d[c] = g(c, 0) + n
    out = []
    for k in sorted(d):
        s = d[k]
        sg = '-' if s < 0 else ''
        s = abs(s)
        out.append('%s,%s%d.%02d' % (k.decode(), sg, s // 100, s % 100))
    sys.stdout.write('\n'.join(out) + '\n')
main()
