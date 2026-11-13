import sys

def slow(data):
    sums = {}
    for line in data.split(b"\n")[1:]:
        p = line.rstrip(b"\r").split(b",")
        if len(p) < 3:
            continue
        try:
            v = float(p[2])
        except ValueError:
            continue
        sums[p[1]] = sums.get(p[1], 0.0) + v
    return sums

def main():
    data = sys.stdin.buffer.read()
    sums = None
    if b"\r" not in data and b"\n\n" not in data:
        t = data.replace(b"\n", b",").split(b",")
        if len(t) % 3 == 1 or len(t) % 3 == 0:
            try:
                sums = {}
                get = sums.get
                for c, v in zip(t[4::3], map(float, t[5::3])):
                    sums[c] = get(c, 0.0) + v
            except ValueError:
                sums = None
    if sums is None:
        sums = slow(data)
    out = [c + b"," + ("%.2f" % sums[c]).encode() + b"\n" for c in sorted(sums)]
    sys.stdout.buffer.write(b"".join(out))

main()
