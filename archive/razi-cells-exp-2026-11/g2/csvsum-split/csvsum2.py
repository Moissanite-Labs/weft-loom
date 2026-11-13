import sys

def main():
    data = sys.stdin.buffer.read()
    # split into lines, skip header
    lines = data.split(b'\n')
    sums = {}
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if not line:
            continue
        # id,cat,val -> find commas
        p1 = line.index(b',')
        p2 = line.index(b',', p1+1)
        cat = line[p1+1:p2]
        try:
            v = float(line[p2+1:])
        except ValueError:
            continue
        sums[cat] = sums.get(cat, 0.0) + v
    out = sys.stdout
    for cat in sorted(sums):
        out.write('%s,%.2f\n' % (cat.decode(), sums[cat]))

main()
