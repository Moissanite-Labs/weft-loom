import bz2

def compress(data: bytes) -> bytes:
    return bz2.compress(data, 9)

def decompress(data: bytes) -> bytes:
    return bz2.decompress(data)
