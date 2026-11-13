"""squeeze.py - exact round-trip compression using only the stdlib.

compress() tries a small portfolio of stdlib back-ends (several tuned LZMA2
filter chains, bzip2, zlib, and a stored fallback) and keeps the smallest
result. A one-byte tag records which back-end won, so decompress() is exact.
"""

import bz2
import lzma
import zlib


def _chain(lc, lp, pb, dict_size):
    return [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME,
             "lc": lc, "lp": lp, "pb": pb, "dict_size": dict_size}]


# Order matters: index in this list is the tag stored in the output.
_CHAINS = [
    _chain(3, 0, 2, 1 << 24),   # lzma defaults (good all-round)
    _chain(3, 0, 0, 1 << 24),   # text: position-independent
    _chain(4, 0, 0, 1 << 24),
    _chain(2, 0, 0, 1 << 24),
    _chain(1, 0, 0, 1 << 24),
    _chain(0, 0, 0, 1 << 24),
    _chain(3, 1, 0, 1 << 24),
    _chain(3, 0, 1, 1 << 24),
    _chain(3, 0, 0, 1 << 26),
]

_TAG_BZ2 = len(_CHAINS)
_TAG_ZLIB = len(_CHAINS) + 1
_TAG_RAW = len(_CHAINS) + 2


def compress(data):
    """Return a compressed representation of *data* (bytes)."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("compress expects bytes")
    data = bytes(data)

    best_tag = _TAG_RAW
    best_body = data

    for i, filters in enumerate(_CHAINS):
        try:
            cand = lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters)
        except Exception:
            continue
        if len(cand) < len(best_body):
            best_tag, best_body = i, cand

    try:
        cand = bz2.compress(data, 9)
        if len(cand) < len(best_body):
            best_tag, best_body = _TAG_BZ2, cand
    except Exception:
        pass

    try:
        cand = zlib.compress(data, 9)
        if len(cand) < len(best_body):
            best_tag, best_body = _TAG_ZLIB, cand
    except Exception:
        pass

    return bytes([best_tag]) + best_body


def decompress(data):
    """Inverse of compress(); exact round-trip guaranteed."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("decompress expects bytes")
    data = bytes(data)
    if not data:
        raise ValueError("empty input")
    tag, body = data[0], data[1:]
    if tag < len(_CHAINS):
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_CHAINS[tag])
    if tag == _TAG_BZ2:
        return bz2.decompress(body)
    if tag == _TAG_ZLIB:
        return zlib.decompress(body)
    if tag == _TAG_RAW:
        return body
    raise ValueError("corrupt data: unknown tag %d" % tag)
