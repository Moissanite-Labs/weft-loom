import lzma, zlib, bz2

# Format: 1 header byte selects codec; rest is payload.
_CODECS = {
    0: (lambda b: b, lambda b: b),
    1: (lambda b: zlib.compress(b, 9), zlib.decompress),
    2: (lambda b: bz2.compress(b, 9), bz2.decompress),
    3: (lambda b: lzma.compress(b, format=lzma.FORMAT_RAW,
                                filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]),
        lambda b: lzma.decompress(b, format=lzma.FORMAT_RAW,
                                  filters=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}])),
}


def compress(data: bytes) -> bytes:
    best = None
    for tag, (enc, _) in _CODECS.items():
        try:
            out = enc(data)
        except Exception:
            continue
        if best is None or len(out) < len(best[1]):
            best = (tag, out)
    return bytes([best[0]]) + best[1]


def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    tag = data[0]
    return _CODECS[tag][1](data[1:])
