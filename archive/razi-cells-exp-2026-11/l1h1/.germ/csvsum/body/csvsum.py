import sys
def main():
    data = sys.stdin.buffer.read().decode().split('\n')
    d = {}
    g = d.get
    for line in data[1:]:
        if not line:
            continue
        p = line.split(',')
        c = p[1]
        d[c] = g(c, 0.0) + float(p[2])
    sys.stdout.write(''.join('%s,%.2f\n' % (k, d[k]) for k in sorted(d)))
main()
