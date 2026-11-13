import lzma

FILTERS = [
    {
        "id": lzma.FILTER_LZMA2,
        "preset": 9 | lzma.PRESET_EXTREME,
        "dict_size": 1 << 23,
        "lc": 3,
        "lp": 0,
        "pb": 0,
        "nice_len": 273,
        "mf": lzma.MF_BT4,
    }
]

def compress(data: bytes) -> bytes:
    if not data:
        return b""
    return lzma.compress(data, format=lzma.FORMAT_RAW, filters=FILTERS)

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    return lzma.decompress(data, format=lzma.FORMAT_RAW, filters=FILTERS)
