import lzma
import bz2
import zlib

_LZMA_FILTERS = [{
    "id": lzma.FILTER_LZMA2,
    "preset": 9 | lzma.PRESET_EXTREME,
    "dict_size": 1 << 23,
    "lc": 3,
    "lp": 0,
    "pb": 2,
    "mf": lzma.MF_BT4,
    "nice_len": 273,
}]

def compress(data: bytes) -> bytes:
    if not data:
        return b"\x00"
    c_lzma = b"\x01" + lzma.compress(data, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)
    c_bz2 = b"\x02" + bz2.compress(data, compresslevel=9)
    c_zlib = b"\x03" + zlib.compress(data, level=9, wbits=-15)
    raw = b"\x00" + data
    return min((c_lzma, c_bz2, c_zlib, raw), key=len)

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    tag = data[0]
    payload = data[1:]
    if tag == 0:
        return payload
    elif tag == 1:
        return lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)
    elif tag == 2:
        return bz2.decompress(payload)
    elif tag == 3:
        return zlib.decompress(payload, wbits=-15)
    raise ValueError("Unknown tag")
