import sys
def main():
    d = {}
    g = d.get
    lines = sys.stdin.buffer.read().split(b"\n")
    for ln in lines[1:]:
        if ln:
            p = ln.split(b",")
            c = p[1]
            d[c] = g(c, 0.0) + float(p[2])
    out = ["%s,%.2f" % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write("\n".join(out) + "\n")
main()
