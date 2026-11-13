import sys

def main():
    data = sys.stdin.buffer.read().split(b"\n", 1)
    if len(data) < 2:
        return
    sums = {}
    get = sums.get
    for line in data[1].split(b"\n"):
        parts = line.split(b",", 2)
        if len(parts) < 3:
            continue
        try:
            v = float(parts[2])
        except ValueError:
            continue
        cat = parts[1]
        sums[cat] = get(cat, 0.0) + v
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + "," + "%.2f" % sums[cat])
    if out:
        sys.stdout.write("\n".join(out) + "\n")

main()
