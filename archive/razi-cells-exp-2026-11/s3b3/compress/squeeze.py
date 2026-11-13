import sys, lzma, bz2
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    out = sys.stdout.buffer
    if m == 'c':
        f = [lzma.FORMAT_RAW]
        filt = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
        a = b'L' + lzma.compress(data, format=lzma.FORMAT_RAW, filters=filt)
        b = b'B' + bz2.compress(data, 9)
        out.write(min(a, b, key=len))
    else:
        t = data[:1]; r = data[1:]
        if t == b'L':
            filt = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
            out.write(lzma.decompress(r, format=lzma.FORMAT_RAW, filters=filt))
        elif t == b'B':
            out.write(bz2.decompress(r))
main()
