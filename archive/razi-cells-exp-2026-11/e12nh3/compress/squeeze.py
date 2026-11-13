import lzma, zlib, bz2
_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 24,
       "lc": 4, "lp": 0, "pb": 0, "nice_len": 273}]

def compress(b):
    c = lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)
    d = bz2.compress(b, 9)
    if len(d) < len(c):
        return b"\x01" + d
    return b"\x00" + c

def decompress(b):
    if not b:
        return b""
    if b[0] == 1:
        return bz2.decompress(b[1:])
    return lzma.decompress(b[1:], format=lzma.FORMAT_RAW, filters=_F)
