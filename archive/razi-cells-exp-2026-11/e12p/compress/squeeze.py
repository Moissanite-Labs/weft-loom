import lzma, bz2, zlib
_F = [dict(id=lzma.FILTER_LZMA2, preset=9 | lzma.PRESET_EXTREME, dict_size=1 << 24, lc=4, lp=0, pb=0)]
def compress(b):
    c = [b'\0' + zlib.compress(b, 9), b'\1' + bz2.compress(b, 9),
         b'\2' + lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)]
    return min(c, key=len)
def decompress(d):
    t, p = d[0], d[1:]
    if t == 0: return zlib.decompress(p)
    if t == 1: return bz2.decompress(p)
    return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=_F)
