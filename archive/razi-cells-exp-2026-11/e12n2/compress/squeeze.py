import lzma, bz2
_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 22}]
def compress(b):
    c = lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)
    z = bz2.compress(b, 9)
    return b"L" + c if len(c) <= len(z) else b"B" + z
def decompress(b):
    if b[:1] == b"L":
        return lzma.decompress(b[1:], format=lzma.FORMAT_RAW, filters=_F)
    return bz2.decompress(b[1:])
