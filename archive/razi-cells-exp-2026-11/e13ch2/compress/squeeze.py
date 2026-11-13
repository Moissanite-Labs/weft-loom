import sys, lzma, bz2
def main():
    m = sys.argv[1]
    d = sys.stdin.buffer.read()
    if m == 'c':
        f = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
        a = b'L' + lzma.compress(d, format=lzma.FORMAT_RAW, filters=f)
        b = b'B' + bz2.compress(d, 9)
        o = a if len(a) < len(b) else b
    else:
        f = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
        t, p = d[:1], d[1:]
        o = lzma.decompress(p, format=lzma.FORMAT_RAW, filters=f) if t == b'L' else bz2.decompress(p)
    sys.stdout.buffer.write(o)
main()
