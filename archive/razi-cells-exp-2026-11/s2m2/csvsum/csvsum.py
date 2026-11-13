import sys


def main():
    data = sys.stdin.buffer.read().split(b"\n")
    sums = {}
    get = sums.get
    for line in data[1:]:
        if not line:
            continue
        parts = line.rstrip(b"\r").split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        try:
            v = float(parts[2])
        except ValueError:
            continue
        sums[cat] = get(cat, 0.0) + v
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + "," + ("%.2f" % sums[cat]))
    if out:
        sys.stdout.write("\n".join(out) + "\n")


main()
