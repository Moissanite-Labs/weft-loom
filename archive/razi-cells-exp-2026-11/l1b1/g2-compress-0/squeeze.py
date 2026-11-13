import sys, lzma
F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 8 << 20,
      "lc": 4, "lp": 0, "pb": 0, "mf": lzma.MF_BT4, "nice_len": 273}]
def main():
    data = sys.stdin.buffer.read()
    if sys.argv[1] == 'c':
        out = lzma.compress(data, format=lzma.FORMAT_RAW, filters=F)
    else:
        out = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=F)
    sys.stdout.buffer.write(out)
main()
