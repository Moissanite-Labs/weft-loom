import sys

def main():
    data = sys.stdin.buffer.read()
    sums = {}
    get = sums.get
    lines = data.split(b"\n")
    for line in lines[1:]:
        if not line:
            continue
        parts = line.split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        sums[cat] = get(cat, 0.0) + float(parts[2])
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + "," + ("%.2f" % sums[cat]))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

main()
