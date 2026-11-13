import sys
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    s = {}
    g = s.get
    for line in data[1:]:
        if not line:
            continue
        a = line.split(b',')
        c = a[1]
        s[c] = g(c, 0.0) + float(a[2])
    out = ['%s,%.2f' % (k.decode(), s[k]) for k in sorted(s)]
    sys.stdout.write('\n'.join(out) + '\n')
main()
