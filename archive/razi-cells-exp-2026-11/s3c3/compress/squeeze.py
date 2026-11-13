import sys
import lzma

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    if sys.argv[1] == "c":
        filters = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 24}]
        out = lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters)
    else:
        filters = [{"id": lzma.FILTER_LZMA2, "dict_size": 1 << 24}]
        out = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=filters)
    sys.stdout.buffer.write(out)

if __name__ == "__main__":
    main()
