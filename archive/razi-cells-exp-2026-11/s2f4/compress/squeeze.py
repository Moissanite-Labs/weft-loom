import sys, lzma, bz2, zlib

def compress(data):
    cands = []
    cands.append(b"L" + lzma.compress(data, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME))
    cands.append(b"B" + bz2.compress(data, 9))
    cands.append(b"Z" + zlib.compress(data, 9))
    return min(cands, key=len)

def decompress(blob):
    tag, body = blob[:1], blob[1:]
    if tag == b"L":
        return lzma.decompress(body)
    if tag == b"B":
        return bz2.decompress(body)
    if tag == b"Z":
        return zlib.decompress(body)
    raise ValueError("bad tag")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("c", "d"):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    out = compress(data) if sys.argv[1] == "c" else decompress(data)
    sys.stdout.buffer.write(out)

if __name__ == "__main__":
    main()
