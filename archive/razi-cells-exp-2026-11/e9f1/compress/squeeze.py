import lzma, re
from collections import Counter

FILTERS = [{"id": lzma.FILTER_LZMA1, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "nice_len": 273}]

def compress(data: bytes) -> bytes:
    used = set(data)
    unused = [b for b in range(256) if b not in used]
    if len(unused) < 16 or len(data) < 256:
        return lzma.compress(b"\x00" + data, format=lzma.FORMAT_RAW, filters=FILTERS)
    pats = re.findall(rb'\n *"[^"]+": |\n *[{}[\],]+|"[a-zA-Z_0-9-]+": ?|"[a-zA-Z0-9_-]+"| [a-zA-Z]+|[A-Z][a-z]+', data)
    counts = Counter(pats)
    scored = sorted(counts.items(), key=lambda kv: kv[1] * (len(kv[0]) - 1), reverse=True)
    tokens = [w for w, c in scored if c * (len(w) - 1) > 40 and 2 <= len(w) <= 250][:len(unused)]
    header = bytearray([1, len(tokens)])
    body = data
    for u, w in zip(unused, tokens):
        header.append(u)
        header.append(len(w))
        header.extend(w)
        body = body.replace(w, bytes([u]))
    return lzma.compress(bytes(header) + body, format=lzma.FORMAT_RAW, filters=FILTERS)

def decompress(data: bytes) -> bytes:
    raw = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=FILTERS)
    if raw[0] == 0:
        return raw[1:]
    k = raw[1]
    pos = 2
    pairs = []
    for _ in range(k):
        u = raw[pos]
        ln = raw[pos + 1]
        w = raw[pos + 2 : pos + 2 + ln]
        pos += 2 + ln
        pairs.append((bytes([u]), w))
    body = raw[pos:]
    for u_b, w in pairs:
        body = body.replace(u_b, w)
    return body
