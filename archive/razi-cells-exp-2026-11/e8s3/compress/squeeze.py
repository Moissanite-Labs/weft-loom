import zlib
import bz2
import lzma

def compress(data: bytes) -> bytes:
    if not data:
        return b"\x00"
    c0 = b"\x00" + data
    c1 = b"\x01" + zlib.compress(data, level=9, wbits=-15)
    c2 = b"\x02" + bz2.compress(data, compresslevel=9)
    c3 = b"\x03" + lzma.compress(data, format=lzma.FORMAT_RAW, filters=[
        {"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}
    ])
    return min((c0, c1, c2, c3), key=len)

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    m = data[0]
    p = data[1:]
    if m == 0:
        return p
    elif m == 1:
        return zlib.decompress(p, wbits=-15)
    elif m == 2:
        return bz2.decompress(p)
    elif m == 3:
        return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=[
            {"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}
        ])
    raise ValueError("Unknown mode")
