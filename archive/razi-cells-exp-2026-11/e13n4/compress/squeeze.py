import sys, lzma, bz2
m = sys.argv[1]
d = sys.stdin.buffer.read()
if m == 'c':
    f = [lzma.FORMAT_RAW]
    flt = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
    a = b'L' + lzma.compress(d, format=lzma.FORMAT_RAW, filters=flt)
    b = b'B' + bz2.compress(d, 9)
    sys.stdout.buffer.write(min(a, b, key=len))
else:
    t, p = d[:1], d[1:]
    if t == b'L':
        flt = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
        o = lzma.decompress(p, format=lzma.FORMAT_RAW, filters=flt)
    elif t == b'B':
        o = bz2.decompress(p)
    else:
        o = b''
    sys.stdout.buffer.write(o)
