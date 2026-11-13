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
        try:
            v = float(p[2])
        except ValueError:
            continue
        c = p[1]
        sums[c] = sums.get(c, 0.0) + v
    out = []
    for c in sorted(sums):
        out.append('%s,%.2f' % (c, sums[c]))
    sys.stdout.write(NL.join(out) + NL)
main()
