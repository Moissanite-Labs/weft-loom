import zlib

def compress(data: bytes) -> bytes:
    if not data:
        return b""
    return zlib.compress(data, level=9)

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    return zlib.decompress(data)
