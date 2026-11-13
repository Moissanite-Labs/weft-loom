import lzma, bz2, zlib
_F = [dict(id=lzma.FILTER_LZMA2, preset=9 | lzma.PRESET_EXTREME, dict_size=1 << 24, lc=4, lp=0, pb=0)]
def compress(b):
    c = [b'\x00' + lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F),
         b'\x01' + bz2.compress(b, 9), b'\x02' + zlib.compress(b, 9)]
    return min(c, key=len)
def decompress(d):
    t, p = d[0], d[1:]
    if t == 0:
        return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=_F)
    return bz2.decompress(p) if t == 1 else zlib.decompress(p)
