import sys


def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b"\n")
    body = data[nl + 1:] if nl >= 0 else b""
    flat = body.replace(b"\r", b"").replace(b"\n", b",").split(b",")
    n = len(flat) // 3
    flat = flat[:n * 3]
    cats = flat[1::3]
    vals = flat[2::3]
    sums = {}
    get = sums.get
    for c, v in zip(cats, vals):
        if v:
            sums[c] = get(c, 0.0) + float(v)
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + "," + ("%.2f" % sums[cat]))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


main()
