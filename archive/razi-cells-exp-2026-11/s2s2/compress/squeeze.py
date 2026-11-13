import sys, lzma, zlib, bz2

def compress(data):
    best = None
    filters = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 22}]
    try:
        c = b"L" + lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters)
        best = c
    except Exception:
        pass
    z = b"Z" + zlib.compress(data, 9)
    if best is None or len(z) < len(best):
        best = z
    b = b"B" + bz2.compress(data, 9)
    if len(b) < len(best):
        best = b
    r = b"R" + data
    if len(r) < len(best):
        best = r
    return best

def decompress(blob):
    tag, body = blob[:1], blob[1:]
    if tag == b"L":
        filters = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 22}]
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=filters)
    if tag == b"Z":
        return zlib.decompress(body)
    if tag == b"B":
        return bz2.decompress(body)
    if tag == b"R":
        return body
    raise ValueError("bad stream")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    out = compress(data) if sys.argv[1] == "c" else decompress(data)
    sys.stdout.buffer.write(out)

if __name__ == "__main__":
    main()
