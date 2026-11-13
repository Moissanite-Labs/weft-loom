import sys
from itertools import compress
def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b"\n")
    body = data[nl+1:].strip(b"\n") if nl >= 0 else b""
    out = []
    if body:
        flat = body.replace(b"\n", b",").split(b",")
        cats = flat[1::3]; vals = flat[2::3]
        for c in sorted(set(cats)):
            s = round(sum(map(float, compress(vals, map(c.__eq__, cats)))), 2) + 0.0
            out.append(f"{c.decode()},{s:.2f}\n")
    sys.stdout.write("".join(out))
main()
