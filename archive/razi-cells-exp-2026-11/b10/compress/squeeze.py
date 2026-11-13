import lzma
import zlib

def compress(data: bytes) -> bytes:
    if not data:
        return b""
    c_lzma = lzma.compress(data, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}])
    c_zlib = zlib.compress(data, level=9, wbits=-15)
    if len(c_zlib) < len(c_lzma):
        return b"\x01" + c_zlib
    return b"\x00" + c_lzma

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    mode = data[0]
    payload = data[1:]
    if mode == 0:
        return lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA2}])
    elif mode == 1:
        return zlib.decompress(payload, wbits=-15)
    raise ValueError("Unknown compression mode")
