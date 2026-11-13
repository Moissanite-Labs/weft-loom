import lzma, bz2, zlib
_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 20}]
def compress(b):
    c = [b"\0" + lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F),
         b"\1" + bz2.compress(b, 9), b"\2" + zlib.compress(b, 9), b"\3" + b]
    return min(c, key=len)
def decompress(d):
    t, p = d[0], d[1:]
    if t == 0: return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=_F)
    if t == 1: return bz2.decompress(p)
    if t == 2: return zlib.decompress(p)
    return p
