import sys, lzma, bz2
def main():
    m = sys.argv[1]
    d = sys.stdin.buffer.read()
    o = sys.stdout.buffer
    if m == 'c':
        f = [lzma.LZMAFilter] if False else None
        a = lzma.compress(d, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 22}])
        b = bz2.compress(d, 9)
        if len(b) < len(a):
            o.write(b'B' + b)
        else:
            o.write(b'L' + a)
    else:
        t, p = d[:1], d[1:]
        if t == b'B':
            o.write(bz2.decompress(p))
        else:
            o.write(lzma.decompress(p, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "dict_size": 1 << 22, "lc": 4, "lp": 0, "pb": 0}]))
main()
