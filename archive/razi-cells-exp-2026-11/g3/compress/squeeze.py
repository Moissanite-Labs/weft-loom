"""squeeze.py - stdlib-only compressor with exact round-trip.

compress(data: bytes) -> bytes
decompress(blob: bytes) -> bytes

Method: 1-byte header selecting the smallest of several raw LZMA1
configurations (tuned for text / JSON), plus bz2, zlib and stored
fallbacks.  Decompression is exact.
"""
import lzma
import zlib
import bz2

_M_LZMA_BASE = 0
_M_BZ2 = 200
_M_ZLIB = 201
_M_STORE = 255

# Raw LZMA1 configurations (no container overhead at all).
_LZMA_CFGS = [
    dict(lc=3, lp=0, pb=2),
    dict(lc=4, lp=0, pb=0),
    dict(lc=3, lp=0, pb=0),
    dict(lc=0, lp=0, pb=0),
    dict(lc=2, lp=0, pb=0),
]


def _filters(cfg):
    f = dict(
        id=lzma.FILTER_LZMA1,
        dict_size=1 << 24,
        mode=lzma.MODE_NORMAL,
        nice_len=273,
        mf=lzma.MF_BT4,
        depth=0,
    )
    f.update(cfg)
    return [f]


_DEC_FILTERS = [_filters(c) for c in _LZMA_CFGS]


def compress(data):
    if not isinstance(data, (bytes, bytearray, memoryview)):
        data = bytes(data)
    data = bytes(data)
    best = bytes([_M_STORE]) + data
    best_n = len(best)

    for i, filt in enumerate(_DEC_FILTERS):
        try:
            c = lzma.compress(data, format=lzma.FORMAT_RAW, filters=filt)
        except Exception:
            continue
        if len(c) + 1 < best_n:
            best = bytes([_M_LZMA_BASE + i]) + c
            best_n = len(best)

    if len(data) > 64:
        c = bz2.compress(data, 9)
        if len(c) + 1 < best_n:
            best = bytes([_M_BZ2]) + c
            best_n = len(best)
        c = zlib.compress(data, 9)
        if len(c) + 1 < best_n:
            best = bytes([_M_ZLIB]) + c
            best_n = len(best)

    return best


def decompress(blob):
    blob = bytes(blob)
    if not blob:
        return b""
    m = blob[0]
    payload = blob[1:]
    if m == _M_STORE:
        return payload
    if m == _M_BZ2:
        return bz2.decompress(payload)
    if m == _M_ZLIB:
        return zlib.decompress(payload)
    idx = m - _M_LZMA_BASE
    if 0 <= idx < len(_DEC_FILTERS):
        return lzma.decompress(payload, format=lzma.FORMAT_RAW,
                               filters=_DEC_FILTERS[idx])
    raise ValueError("unknown compression method %r" % (m,))
