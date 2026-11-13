import sys
import bz2
import lzma


def compress(data):
    best = b"B" + bz2.compress(data, 9)
    try:
        lz = lzma.compress(data, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME)
        if len(lz) + 1 < len(best):
            best = b"L" + lz
    except Exception:
        pass
    return best


def decompress(blob):
    tag, body = blob[:1], blob[1:]
    if tag == b"L":
        return lzma.decompress(body, format=lzma.FORMAT_ALONE)
    if tag == b"B":
        return bz2.decompress(body)
    raise ValueError("unknown tag")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    out = compress(data) if sys.argv[1] == "c" else decompress(data)
    sys.stdout.buffer.write(out)


if __name__ == "__main__":
    main()
