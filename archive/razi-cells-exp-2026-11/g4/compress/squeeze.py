"""Squeeze: word-tokenised stream, best of bz2 / lzma(raw tuned) / lzma(xz)."""
import bz2
import lzma
import zlib

ESC = 127
WORD_LIMIT = 128
RAW = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME,
        "lc": 3, "pb": 0}]


def _words(data):
    from collections import Counter
    cnt = Counter()
    n = len(data)
    i = 0
    while i < n:
        b = data[i]
        if 65 <= b <= 90 or 97 <= b <= 122:
            j = i + 1
            while j < n:
                c = data[j]
                if 65 <= c <= 90 or 97 <= c <= 122:
                    j += 1
                else:
                    break
            if j - i >= 3:
                cnt[data[i:j]] += 1
            i = j
        else:
            i += 1
    scored = []
    for w, c in cnt.items():
        if c < 2 or len(w) > 60:
            continue
        gain = (len(w) - 1) * c - len(w) - 2
        if gain > 4:
            scored.append((gain, w))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [w for _, w in scored[:WORD_LIMIT]]


def _pack(words):
    out = bytearray([len(words)])
    for w in words:
        out.append(len(w))
        out += w
    return bytes(out)


def _unpack(data):
    k = data[0]
    pos = 1
    words = []
    for _ in range(k):
        ln = data[pos]
        words.append(data[pos + 1:pos + 1 + ln])
        pos += 1 + ln
    return words, data[pos:]


def _encode(data, words):
    idx = {w: i for i, w in enumerate(words)}
    by1 = {}
    for w in words:
        by1.setdefault(w[0], []).append(w)
    for k in by1:
        by1[k].sort(key=len, reverse=True)
    out = bytearray()
    n = len(data)
    i = 0
    while i < n:
        b = data[i]
        lst = by1.get(b)
        if lst:
            hit = None
            for w in lst:
                if data.startswith(w, i):
                    hit = w
                    break
            if hit is not None:
                out.append(128 + idx[hit])
                i += len(hit)
                continue
        if b >= ESC:
            out.append(ESC)
        out.append(b)
        i += 1
    return bytes(out)


def _decode(data, words):
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == ESC:
            out.append(data[i + 1])
            i += 2
        elif b >= 128:
            out += words[b - 128]
            i += 1
        else:
            out.append(b)
            i += 1
    return bytes(out)


def compress(data: bytes) -> bytes:
    best = None
    words = _words(data)
    if words:
        pre = _pack(words) + _encode(data, words)
        for tag, blob in ((b"\x10", lambda: bz2.compress(pre, 9)),
                          (b"\x11", lambda: lzma.compress(pre, preset=9 | lzma.PRESET_EXTREME)),
                          (b"\x12", lambda: lzma.compress(pre, format=lzma.FORMAT_RAW, filters=RAW))):
            try:
                c = tag + blob()
            except Exception:
                continue
            if best is None or len(c) < len(best):
                best = c
    for tag, blob in ((b"\x02", lambda: bz2.compress(data, 9)),
                      (b"\x01", lambda: lzma.compress(data, preset=9 | lzma.PRESET_EXTREME)),
                      (b"\x03", lambda: zlib.compress(data, 9))):
        try:
            c = tag + blob()
        except Exception:
            continue
        if best is None or len(c) < len(best):
            best = c
    return best


def decompress(data: bytes) -> bytes:
    tag = data[0]
    body = data[1:]
    if tag == 16:
        words, rest = _unpack(bz2.decompress(body))
        return _decode(rest, words)
    if tag == 17:
        words, rest = _unpack(lzma.decompress(body))
        return _decode(rest, words)
    if tag == 18:
        words, rest = _unpack(lzma.decompress(body, format=lzma.FORMAT_RAW, filters=RAW))
        return _decode(rest, words)
    if tag == 2:
        return bz2.decompress(body)
    if tag == 1:
        return lzma.decompress(body)
    if tag == 3:
        return zlib.decompress(body)
    raise ValueError("bad tag")
