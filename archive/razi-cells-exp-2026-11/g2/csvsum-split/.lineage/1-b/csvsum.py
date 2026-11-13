import sys


def main():
    f = sys.stdin.buffer
    f.readline()  # header: id,cat,val
    sums = {}
    get = sums.get
    for line in f:
        if not line:
            continue
        p = line.split(b',')
        if len(p) < 3:
            continue
        cat = p[1]
        v = p[2]
        if v and v[-1] == 10:  # newline
            v = v[:-1]
            if v and v[-1] == 13:  # crlf
                v = v[:-1]

        neg = False
        if v[:1] == b'-':
            neg = True
            v = v[1:]

        dot = v.find(b'.')
        if dot < 0:
            cents = int(v) * 100
        else:
            whole = v[:dot]
            frac = v[dot + 1:]
            w = int(whole) if whole else 0
            if len(frac) == 0:
                fr = 0
            elif len(frac) == 1:
                fr = (frac[0] - 48) * 10
            else:
                fr = (frac[0] - 48) * 10 + (frac[1] - 48)
            cents = w * 100 + fr
        if neg:
            cents = -cents

        sums[cat] = get(cat, 0) + cents

    out = sys.stdout.buffer
    for cat in sorted(sums):
        t = sums[cat]
        sign = b'-' if t < 0 else b''
        if t < 0:
            t = -t
        out.write(b'%s,%s%d.%02d\n' % (cat, sign, t // 100, t % 100))


if __name__ == '__main__':
    main()
