import sys, math

def main():
    data = sys.stdin.buffer.read().split(b'\n')
    groups = {}
    for line in data[1:]:
        if not line:
            continue
        parts = line.rstrip(b'\r').split(b',')
        if len(parts) < 3:
            continue
        c = parts[1]
        v = float(parts[2])
        g = groups.get(c)
        if g is None:
            groups[c] = [v]
        else:
            g.append(v)
    out = []
    for c in sorted(groups):
        out.append(c.decode() + ',' + ('%.2f' % math.fsum(groups[c])))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))

main()
