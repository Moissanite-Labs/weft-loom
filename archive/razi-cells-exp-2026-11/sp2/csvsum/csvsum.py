import sys


def main():
    lines = sys.stdin.buffer.read().split(b"\n")
    sums = {}
    get = sums.get
    for line in lines[1:]:
        parts = line.split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        sums[cat] = get(cat, 0.0) + float(parts[2])
    out = []
    for cat in sorted(sums):
        out.append("%s,%.2f" % (cat.decode(), sums[cat]))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()
