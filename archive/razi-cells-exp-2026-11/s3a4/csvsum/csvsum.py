import sys, math

def main():
    data = sys.stdin.buffer.read().split(b"\n")
    groups = {}
    get = groups.get
    for line in data[1:]:
        if not line:
            continue
        parts = line.split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        v = float(parts[2])
        lst = get(cat)
        if lst is None:
            groups[cat] = [v]
        else:
            lst.append(v)
    out = []
    for cat in sorted(groups):
        s = math.fsum(groups[cat])
        out.append(cat.decode() + "," + ("%.2f" % s))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

main()
