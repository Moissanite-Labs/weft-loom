import sys
import math


def main():
    data = sys.stdin.buffer.read().split(b"\n")
    groups = {}
    get = groups.get
    for line in data[1:]:
        if not line:
            continue
        parts = line.rstrip(b"\r").split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        lst = get(cat)
        if lst is None:
            lst = []
            groups[cat] = lst
        lst.append(float(parts[2]))
    out = []
    for cat in sorted(groups):
        out.append(cat.decode() + "," + ("%.2f" % math.fsum(groups[cat])))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
