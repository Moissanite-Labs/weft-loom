import sys


def fmt(sums):
    out = []
    for cat in sorted(sums):
        t = sums[cat]
        sign = "-" if t < 0 else ""
        t = abs(t)
        out.append(cat + b"," + ("%s%d.%02d" % (sign, t // 100, t % 100)).encode())
    sys.stdout.buffer.write(b"\n".join(out) + (b"\n" if out else b""))


def slow(data):
    text = data.decode("utf-8", "replace")
    sums = {}
    first = True
    for line in text.splitlines():
        if first:
            first = False
            if line.strip().lower().startswith("id"):
                continue
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 3:
            continue
        cat = parts[1].strip().encode("utf-8")
        try:
            c = round(float(parts[2].strip()) * 100)
        except ValueError:
            continue
        sums[cat] = sums.get(cat, 0) + c
    fmt(sums)


def main():
    data = sys.stdin.buffer.read()
    if b'"' in data or b"\r" in data or b" " in data or b"\t" in data:
        slow(data)
        return
    toks = data.replace(b",", b" ").split()
    if toks and toks[0].lower() == b"id":
        toks = toks[3:]
    sums = {}
    get = sums.get
    for c, v in zip(toks[1::3], toks[2::3]):
        try:
            x = round(float(v) * 100)
        except ValueError:
            continue
        sums[c] = get(c, 0) + x
    fmt(sums)


if __name__ == "__main__":
    main()
