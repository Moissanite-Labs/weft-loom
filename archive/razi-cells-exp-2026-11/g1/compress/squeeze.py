import bz2, lzma, zlib

# raw LZMA1 tuning that scored best on the mixed text/JSON corpus
_LZMA_FILTERS = [
    {'id': lzma.FILTER_LZMA1, 'preset': 9 | lzma.PRESET_EXTREME,
     'lc': 2, 'lp': 0, 'pb': 0},
    {'id': lzma.FILTER_LZMA1, 'preset': 9 | lzma.PRESET_EXTREME,
     'lc': 3, 'lp': 0, 'pb': 0},
]

TAG_BZ2 = 0
TAG_LZMA = 1  # followed by a filter-index byte
TAG_ZLIB = 2
TAG_STORE = 3


def _candidates(data):
    yield TAG_BZ2, bz2.compress(data, 9)
    for i, f in enumerate(_LZMA_FILTERS):
        try:
            yield TAG_LZMA, bytes([i]) + lzma.compress(
                data, format=lzma.FORMAT_RAW, filters=[f])
        except Exception:
            pass
    yield TAG_ZLIB, zlib.compress(data, 9)
    yield TAG_STORE, data


def compress(data):
    data = bytes(data)
    best_tag, best_blob = min(_candidates(data), key=lambda tb: len(tb[1]))
    return bytes([best_tag]) + best_blob


def decompress(blob):
    blob = bytes(blob)
    tag, body = blob[0], blob[1:]
    if tag == TAG_BZ2:
        return bz2.decompress(body)
    if tag == TAG_LZMA:
        return lzma.decompress(body[1:], format=lzma.FORMAT_RAW,
                               filters=[_LZMA_FILTERS[body[0]]])
    if tag == TAG_ZLIB:
        return zlib.decompress(body)
    if tag == TAG_STORE:
        return body
    raise ValueError('bad tag %r' % (tag,))


if __name__ == '__main__':
    import bench
    d = bench.corpus()
    c = compress(d)
    assert decompress(c) == d
    print('len %d -> %d  ratio %.4f' % (len(d), len(c), len(d) / len(c)))
