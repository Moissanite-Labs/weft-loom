import sys
from collections import Counter

def main():
    tbl = bytearray(b' ' * 256)
    for i in range(97, 123):
        tbl[i] = i
        tbl[i - 32] = i
    tbl = bytes(tbl)
    data = sys.stdin.buffer.read()
    c = Counter(data.translate(tbl).split())
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join(f"{w.decode()} {n}\n" for w, n in top))

main()
