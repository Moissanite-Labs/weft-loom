import lzma
import bz2

FILTERS = [{"id": lzma.FILTER_LZMA1, "preset": 9 | lzma.PRESET_EXTREME, "lc": 3, "lp": 0, "pb": 0, "nice_len": 273}]

def compress(data: bytes) -> bytes:
    if not data:
        return b""
    c_lzma = lzma.compress(data, format=lzma.FORMAT_RAW, filters=FILTERS)
    c_bz2 = bz2.compress(data, 9)
    if len(c_bz2) < len(c_lzma):
        return b"\x01" + c_bz2
    return b"\x00" + c_lzma

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    if data[0] == 1:
        return bz2.decompress(data[1:])
    return lzma.decompress(data[1:], format=lzma.FORMAT_RAW, filters=FILTERS)
