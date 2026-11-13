import lzma, re
from collections import Counter

_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "nice_len": 273, "depth": 0}]
_WORD = re.compile(rb' ?[A-Za-z]{2,}')

def _lz(b): return lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)
def _unlz(b): return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=_F)

def _code(i):
    if i < 64: return bytes([192 + i])
    i -= 64
    return bytes([128 + (i >> 8), i & 255])

def _fwd(data):
    cnt = Counter(m.group() for m in _WORD.finditer(data))
    words = [w for w, c in cnt.most_common(64 + 64 * 256) if c * len(w) >= 6]
    tab = {w: _code(i) for i, w in enumerate(words)}
    body = _WORD.sub(lambda m: tab.get(m.group(), m.group()), data)
    return b'|'.join(words) + b'\n' + body

def _inv(blob):
    i = blob.index(b'\n')
    words = blob[:i].split(b'|') if i else []
    body = blob[i + 1:]
    out = bytearray(); j = 0; n = len(body)
    while j < n:
        b = body[j]
        if b < 128: out.append(b); j += 1
        elif b >= 192: out += words[b - 192]; j += 1
        else:
            out += words[64 + ((b - 128) << 8) + body[j + 1]]; j += 2
    return bytes(out)

def compress(data):
    cands = [b'\0' + _lz(data)]
    if data.isascii():
        cands.append(b'\1' + _lz(_fwd(data)))
    return min(cands, key=len)

def decompress(data):
    if not data: return b''
    if data[0] == 0: return _unlz(data[1:])
    return _inv(_unlz(data[1:]))
