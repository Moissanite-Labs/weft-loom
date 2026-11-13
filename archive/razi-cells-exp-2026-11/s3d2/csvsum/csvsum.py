import sys
def main():
    t = sys.stdin.buffer.read().replace(b',', b' ').split()
    cats = t[4::3]
    vals = map(float, t[5::3])
    d = {}
    g = d.get
    for c, v in zip(cats, vals):
        d[c] = g(c, 0.0) + v
    out = [f"{k.decode()},{d[k]:.2f}" for k in sorted(d)]
    sys.stdout.write("\n".join(out) + "\n")
main()
