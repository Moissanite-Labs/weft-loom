import lzma, bz2, zlib
_F = [dict(id=lzma.FILTER_LZMA2, preset=9 | lzma.PRESET_EXTREME, lc=4, lp=0, pb=0, dict_size=1 << 24)]
def compress(b):
    c = [b'\0' + lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F), b'\1' + bz2.compress(b, 9), b'\2' + zlib.compress(b, 9)]
    return min(c, key=len)
def decompress(b):
    t, d = b[0], b[1:]
    if t == 0: return lzma.decompress(d, format=lzma.FORMAT_RAW, filters=_F)
    if t == 1: return bz2.decompress(d)
    return zlib.decompress(d)
