import sys, bz2, lzma

def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    out = sys.stdout.buffer
    if m == 'c':
        a = b'B' + bz2.compress(data, 9)
        f = [{"id": lzma.FILTER_LZMA1, "preset": 9 | lzma.PRESET_EXTREME}]
        b = b'L' + lzma.compress(data, format=lzma.FORMAT_ALONE, filters=f)
        out.write(a if len(a) <= len(b) else b)
    else:
        t, p = data[:1], data[1:]
        if t == b'B':
            out.write(bz2.decompress(p))
        else:
            out.write(lzma.decompress(p, format=lzma.FORMAT_ALONE))

main()
