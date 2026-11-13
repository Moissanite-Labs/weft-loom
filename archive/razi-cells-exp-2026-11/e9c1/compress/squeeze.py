import lzma

def compress(data: bytes) -> bytes:
    if not data:
        return b""
    return lzma.compress(data, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}])

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    return lzma.decompress(data, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2}])
