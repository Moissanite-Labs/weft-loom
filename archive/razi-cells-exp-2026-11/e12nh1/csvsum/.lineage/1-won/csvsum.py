import sys
from collections import defaultdict
def main():
    data = sys.stdin.buffer.read()
    toks = data.replace(b"\n", b",").split(b",")
    if toks and toks[-1] == b"": toks.pop()
    d = defaultdict(float)
    for c, v in zip(toks[4::3], toks[5::3]):
        d[c] += float(v)
    out = ["%s %.2f" % (k.decode(), d[k]) for k in sorted(d)]
    print("\n".join(out))
main()
