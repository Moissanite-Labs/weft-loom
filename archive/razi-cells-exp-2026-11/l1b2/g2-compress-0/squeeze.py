import sys, bz2, lzma
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    if m == 'c':
        a = b'b' + bz2.compress(data, 9)
        f = [{"id": lzma.FILTER_LZMA1, "preset": 9 | lzma.PRESET_EXTREME}]
        l = b'l' + lzma.compress(data, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME)
        out = min(a, l, key=len)
    else:
        t, r = data[:1], data[1:]
        if t == b'b':
            out = bz2.decompress(r)
        else:
            out = lzma.decompress(r, format=lzma.FORMAT_ALONE)
    sys.stdout.buffer.write(out)
main()
