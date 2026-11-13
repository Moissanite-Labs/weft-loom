import sys, lzma

FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 20}]

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    data = sys.stdin.buffer.read()
    if mode == "c":
        out = lzma.compress(data, format=lzma.FORMAT_RAW, filters=FILTERS)
    elif mode == "d":
        out = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=FILTERS)
    else:
        sys.exit("usage: squeeze.py c|d")
    sys.stdout.buffer.write(out)

if __name__ == "__main__":
    main()
