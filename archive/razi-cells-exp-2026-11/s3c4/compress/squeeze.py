import sys, lzma, bz2, zlib

def compress(data):
    best = None
    cands = [
        (b'L', lzma.compress(data, format=lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME)),
        (b'B', bz2.compress(data, 9)),
        (b'Z', zlib.compress(data, 9)),
    ]
    for tag, out in cands:
        if best is None or len(out) < len(best):
            best = tag + out
    return best

def decompress(blob):
    tag, body = blob[:1], blob[1:]
    if tag == b'L':
        return lzma.decompress(body)
    if tag == b'B':
        return bz2.decompress(body)
    if tag == b'Z':
        return zlib.decompress(body)
    raise ValueError('bad tag')

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('c', 'd'):
        sys.stderr.write('usage: squeeze.py c|d\n')
        sys.exit(2)
    data = sys.stdin.buffer.read()
    out = compress(data) if sys.argv[1] == 'c' else decompress(data)
    sys.stdout.buffer.write(out)

if __name__ == '__main__':
    main()
