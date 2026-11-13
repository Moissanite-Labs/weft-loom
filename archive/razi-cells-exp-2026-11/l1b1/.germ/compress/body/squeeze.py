import sys, bz2, lzma, zlib
def main():
    m = sys.argv[1]
    data = sys.stdin.buffer.read()
    o = sys.stdout.buffer
    if m == 'c':
        c = [b'\x00' + bz2.compress(data, 9),
             b'\x01' + lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)]
        o.write(min(c, key=len))
    else:
        if not data:
            return
        t = data[0]; b = data[1:]
        o.write(bz2.decompress(b) if t == 0 else lzma.decompress(b))
main()
