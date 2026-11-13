import lzma, bz2, zlib
def _lz(d, lc, lp, pb):
    f = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": lc, "lp": lp, "pb": pb, "dict_size": 1 << 24}]
    return lzma.compress(d, format=lzma.FORMAT_RAW, filters=f)
_P = [(3, 0, 0), (4, 0, 0), (3, 0, 2)]
def compress(data):
    best = b"\x00" + data
    c = b"\x01" + bz2.compress(data, 9)
    if len(c) < len(best): best = c
    for i, p in enumerate(_P):
        c = bytes([2 + i]) + _lz(data, *p)
        if len(c) < len(best): best = c
    return best
def decompress(blob):
    t, d = blob[0], blob[1:]
    if t == 0: return d
    if t == 1: return bz2.decompress(d)
    lc, lp, pb = _P[t - 2]
    f = [{"id": lzma.FILTER_LZMA2, "lc": lc, "lp": lp, "pb": pb, "dict_size": 1 << 24}]
    return lzma.decompress(d, format=lzma.FORMAT_RAW, filters=f)
