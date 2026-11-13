import sys


def main():
    data = sys.stdin.buffer.read()
    sums = {}
    get = sums.get
    for line in data.split(b"\n")[1:]:
        parts = line.split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        sums[cat] = get(cat, 0.0) + float(parts[2])
    out = [b"%s,%.2f" % (c, sums[c]) for c in sorted(sums)]
    sys.stdout.buffer.write(b"\n".join(out) + (b"\n" if out else b""))


if __name__ == "__main__":
    main()
