import sys

def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b'\n')
    if nl < 0:
        return
    body = data[nl+1:]
    sums = {}
    comps = {}
    sget = sums.get
    cget = comps.get
    i_find = b'\n'
    for line in body.split(b'\n'):
        if not line:
            continue
        if line[-1:] == b'\r':
            line = line[:-1]
        i = line.find(b',')
        j = line.find(b',', i+1)
        if j < 0:
            continue
        cat = line[i+1:j]
        v = float(line[j+1:])
        s = sget(cat, 0.0)
        c = cget(cat, 0.0)
        y = v - c
        t = s + y
        comps[cat] = (t - s) - y
        sums[cat] = t
    out = sys.stdout
    for cat in sorted(sums):
        v = sums[cat]
        out.write('%s,%.2f\n' % (cat.decode(), v))

main()
