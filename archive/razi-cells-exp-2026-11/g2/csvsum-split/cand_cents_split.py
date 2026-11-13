import sys
NL = chr(10)
def main():
    inp = sys.stdin
    next(inp, None)
    sums = {}
    for line in inp:
        p = line.split(',')
        if len(p) < 3:
            continue
        s = p[2].strip()
        neg = s[:1] == '-'
        if neg:
            s = s[1:]
        if '.' in s:
            w, fr = s.split('.', 1)
            fr = (fr + '00')[:2]
        else:
            w, fr = s, '00'
        try:
            v = int(w) * 100 + int(fr)
        except ValueError:
            continue
        if neg:
            v = -v
        c = p[1]
        sums[c] = sums.get(c, 0) + v
    out = []
    for c in sorted(sums):
        t = sums[c]
        sign = '-' if t < 0 else ''
        t = abs(t)
        out.append('%s,%s%d.%02d' % (c, sign, t // 100, t % 100))
    sys.stdout.write(NL.join(out) + NL)
main()
