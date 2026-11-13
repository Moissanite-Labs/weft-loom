import sys, lzma, bz2, zlib
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    out = sys.stdout.buffer
    if m == 'c':
        f = [lzma.FILTER_LZMA2]
        c = []
        flt = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
        c.append(b'\x00' + lzma.compress(data, format=lzma.FORMAT_RAW, filters=flt))
        c.append(b'\x01' + bz2.compress(data, 9))
        out.write(min(c, key=len))
    else:
        t = data[:1]; b = data[1:]
        if t == b'\x00':
            flt = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 24}]
            out.write(lzma.decompress(b, format=lzma.FORMAT_RAW, filters=flt))
        else:
            out.write(bz2.decompress(b))
main()
