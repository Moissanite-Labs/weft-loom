import sys, lzma, bz2

def compress(data):
    cands = [b'\x00' + bz2.compress(data, 9),
             b'\x01' + lzma.compress(data, format=lzma.FORMAT_ALONE,
                                     preset=9 | lzma.PRESET_EXTREME)]
    return min(cands, key=len)

def decompress(blob):
    tag, body = blob[:1], blob[1:]
    if tag == b'\x00':
        return bz2.decompress(body)
    return lzma.decompress(body, format=lzma.FORMAT_ALONE)

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('c', 'd'):
        sys.stderr.write('usage: squeeze.py c|d\n')
        sys.exit(2)
    data = sys.stdin.buffer.read()
    out = compress(data) if sys.argv[1] == 'c' else decompress(data)
    sys.stdout.buffer.write(out)

if __name__ == '__main__':
    main()
