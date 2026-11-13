import sys
import lzma
import bz2

FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 22}]


def compress(data):
    cands = [b'\x00' + bz2.compress(data, 9),
             b'\x01' + lzma.compress(data, format=lzma.FORMAT_RAW, filters=FILTERS)]
    return min(cands, key=len)


def decompress(data):
    tag, body = data[:1], data[1:]
    if tag == b'\x00':
        return bz2.decompress(body)
    return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=FILTERS)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        return 2
    data = sys.stdin.buffer.read()
    out = compress(data) if sys.argv[1] == "c" else decompress(data)
    sys.stdout.buffer.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
