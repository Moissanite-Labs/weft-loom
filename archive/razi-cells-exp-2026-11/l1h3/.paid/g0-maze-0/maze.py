import sys
def main():
    data = sys.stdin.buffer.read().replace(b'\r', b'').strip(b'\n')
    lines = data.split(b'\n')
    st = max(len(l) for l in lines) + 1
    if any(len(l) != st - 1 for l in lines):
        data = b'\n'.join(l.ljust(st - 1, b'#') for l in lines)
    N = len(data)
    si = data.find(b'S'); ei = data.find(b'E')
    if si < 0 or ei < 0:
        print(-1); return
    tbl = bytearray(b'0' * 256)
    for c in b'.SE': tbl[c] = 49
    free = int(data.translate(bytes(tbl)), 2)
    f = 1 << (N - 1 - si)
    e = 1 << (N - 1 - ei)
    free &= ~f
    d = 0
    while f:
        if f & e:
            print(d); return
        f = ((f << 1) | (f >> 1) | (f << st) | (f >> st)) & free
        free ^= f
        d += 1
    print(-1)
main()
