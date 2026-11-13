import sys
import lzma

FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 3, "lp": 0, "pb": 0}]


def compress(data):
    return lzma.compress(data, format=lzma.FORMAT_RAW, filters=FILTERS)


def decompress(data):
    return lzma.decompress(data, format=lzma.FORMAT_RAW, filters=FILTERS)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    if sys.argv[1] == "c":
        out = compress(data)
    else:
        out = decompress(data)
    sys.stdout.buffer.write(out)


if __name__ == "__main__":
    main()
