import sys
def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b'\n')
    d = {}
    get = d.get
    for line in lines[1:]:
        if line:
            _, c, v = line.split(b',')
            d[c] = get(c, 0.0) + float(v)
    out = ['%s,%.2f\n' % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write(''.join(out))
main()
