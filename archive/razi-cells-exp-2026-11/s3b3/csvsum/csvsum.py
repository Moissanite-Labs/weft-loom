import sys
def main():
    t = sys.stdin.buffer.read().replace(b',', b'\n').split()
    d = {}
    g = d.get
    for c, v in zip(t[4::3], t[5::3]):
        d[c] = g(c, 0.0) + float(v)
    out = []
    for c in sorted(d):
        out.append("%s,%.2f" % (c.decode(), d[c]))
    sys.stdout.write("\n".join(out) + "\n")
main()
