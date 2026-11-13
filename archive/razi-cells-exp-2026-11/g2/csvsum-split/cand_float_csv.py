import sys, csv
NL = chr(10)
def main():
    r = csv.reader(sys.stdin)
    next(r, None)
    sums = {}
    for row in r:
        if len(row) < 3:
            continue
        try:
            v = float(row[2])
        except ValueError:
            continue
        c = row[1]
        sums[c] = sums.get(c, 0.0) + v
    out = []
    for c in sorted(sums):
        out.append('%s,%.2f' % (c, sums[c]))
    sys.stdout.write(NL.join(out) + NL)
main()
