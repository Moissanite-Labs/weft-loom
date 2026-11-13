import sys, bz2, lzma, zlib

METHODS = [
    (b'\x00', lambda d: d, lambda d: d),
    (b'\x01', lambda d: bz2.compress(d, 9), bz2.decompress),
    (b'\x02', lambda d: lzma.compress(d, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME), lzma.decompress),
    (b'\x03', lambda d: zlib.compress(d, 9), zlib.decompress),
]


def compress(data):
    best = None
    for tag, enc, _ in METHODS:
        out = tag + enc(data)
        if best is None or len(out) < len(best):
            best = out
    return best


def decompress(blob):
    tag = blob[:1]
    for t, _, dec in METHODS:
        if t == tag:
            return dec(blob[1:])
    raise ValueError("unknown method")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('c', 'd'):
        sys.stderr.write("usage: squeeze.py c|d\n")
        sys.exit(2)
    data = sys.stdin.buffer.read()
    if sys.argv[1] == 'c':
        out = compress(data)
    else:
        out = decompress(data)
    sys.stdout.buffer.write(out)


if __name__ == '__main__':
    main()
