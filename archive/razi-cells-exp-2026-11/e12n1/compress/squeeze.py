import lzma, bz2, zlib
F = [dict(id=lzma.FILTER_LZMA2, preset=9 | lzma.PRESET_EXTREME, dict_size=1 << 24, lc=4, lp=0, pb=0)]
def compress(b):
    c = [b'\0' + b,
         b'\1' + lzma.compress(b, format=lzma.FORMAT_RAW, filters=F),
         b'\2' + bz2.compress(b, 9),
         b'\3' + zlib.compress(b, 9)]
    return min(c, key=len)
def decompress(d):
    t, p = d[0], d[1:]
    if t == 0: return p
    if t == 1: return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=F)
    if t == 2: return bz2.decompress(p)
    return zlib.decompress(p)
