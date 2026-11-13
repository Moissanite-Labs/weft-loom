import lzma, zlib
_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "dict_size": 1 << 24,
       "lc": 4, "lp": 0, "pb": 0, "mf": lzma.MF_BT4, "nice_len": 273, "depth": 1000}]
def compress(b):
    return lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)
def decompress(b):
    return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=_F)
