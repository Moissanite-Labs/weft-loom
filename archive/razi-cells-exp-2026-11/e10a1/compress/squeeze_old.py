"""squeeze: stdlib-only compressor. Picks the smallest of several codecs; 1-byte tag."""
import lzma, bz2, zlib

_LZ_FILTERS = [
    [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}],
    [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0}],
    [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 3, "lp": 0, "pb": 0}],
]


def compress(data: bytes) -> bytes:
    data = bytes(data)
    best = b"\x00" + data  # stored
    for i, f in enumerate(_LZ_FILTERS):
        c = bytes([1 + i]) + lzma.compress(data, format=lzma.FORMAT_RAW, filters=f)
        if len(c) < len(best):
            best = c
    c = b"\x10" + bz2.compress(data, 9)
    if len(c) < len(best):
        best = c
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    c = b"\x11" + co.compress(data) + co.flush()
    if len(c) < len(best):
        best = c
    return best


def decompress(blob: bytes) -> bytes:
    blob = bytes(blob)
    if not blob:
        raise ValueError("empty input")
    tag, body = blob[0], blob[1:]
    if tag == 0:
        return body
    if 1 <= tag <= len(_LZ_FILTERS):
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_LZ_FILTERS[tag - 1])
    if tag == 0x10:
        return bz2.decompress(body)
    if tag == 0x11:
        return zlib.decompress(body, -15)
    raise ValueError("bad tag")
