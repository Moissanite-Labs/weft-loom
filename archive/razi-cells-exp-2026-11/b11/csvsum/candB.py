import sys
import numpy as np
def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b"\n")
    body = data[nl+1:].strip(b"\n") if nl >= 0 else b""
    out = []
    if body:
        flat = body.replace(b"\n", b",").split(b",")
        cats = np.array(flat[1::3])
        vals = np.fromstring(b" ".join(flat[2::3]), dtype=np.float64, sep=" ")
        for c in sorted(set(flat[1::3])):
            s = round(float(vals[cats == c].sum()), 2) + 0.0
            out.append(f"{c.decode()},{s:.2f}\n")
    sys.stdout.write("".join(out))
main()
