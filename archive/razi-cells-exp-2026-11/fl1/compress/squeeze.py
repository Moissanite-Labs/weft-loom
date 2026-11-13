import sys, lzma, bz2, zlib
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    out = sys.stdout.buffer
    if m == 'c':
        f = [lzma.LZMAFilter] if False else None
        c = [b'L' + lzma.compress(data, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]),
             b'B' + bz2.compress(data, 9)]
        out.write(min(c, key=len))
    else:
        t, b = data[:1], data[1:]
        if t == b'L':
            out.write(lzma.decompress(b, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]))
        elif t == b'B':
            out.write(bz2.decompress(b))
main()
