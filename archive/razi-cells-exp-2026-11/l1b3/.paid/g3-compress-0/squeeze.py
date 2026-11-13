import sys, lzma
F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 20, "lc": 4, "lp": 0, "pb": 0}]
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    if m == "c":
        out = lzma.compress(data, format=lzma.FORMAT_RAW, filters=F)
    else:
        out = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=F)
    sys.stdout.buffer.write(out)
main()
