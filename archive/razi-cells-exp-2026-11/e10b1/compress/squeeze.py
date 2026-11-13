"""squeeze: stdlib-only compressor. Tries several codecs, keeps the smallest.

Format: 1 tag byte + payload.
  0 = raw, 1 = zlib, 2 = bz2, 16..20 = raw LZMA2 variants,
  32 = word model (word/separator tokens, static order-0 range coder),
  33 = two independently compressed segments (split at a text/non-text changepoint).
"""
import re
import zlib
import bz2
import lzma
from bisect import bisect_right
from collections import Counter
from itertools import accumulate

_LZMA = {}
_t = 16
for _lc, _lp, _pb in ((3, 0, 0), (4, 0, 0), (3, 0, 2), (2, 0, 0), (0, 0, 0)):
    _LZMA[_t] = [{
        "id": lzma.FILTER_LZMA2,
        "preset": 9 | lzma.PRESET_EXTREME,
        "dict_size": 1 << 26,
        "lc": _lc, "lp": _lp, "pb": _pb,
        "nice_len": 273,
        "mf": lzma.MF_BT4,
        "depth": 0,
    }]
    _t += 1

_TOK = re.compile(rb"[A-Za-z]+|[^A-Za-z]+")
_SENT = re.compile(rb"[.!?]")
_TOP = 1 << 64
_BOT = 1 << 56
_HI = 0xFF << 56
_M56 = _BOT - 1
_LIM = 1 << 24
_CLS = bytes(1 if (i == 32 or 65 <= i <= 90 or 97 <= i <= 122) else 0 for i in range(256))


def _varint(n, out):
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)


def _getvar(buf, pos):
    n = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if b < 0x80:
            return n, pos
        shift += 7


# ---------- generic codecs ----------
def _pack(data):
    best = b"\x00" + data
    cands = []
    try:
        cands.append(b"\x01" + zlib.compress(data, 9))
    except Exception:
        pass
    try:
        cands.append(b"\x02" + bz2.compress(data, 9))
    except Exception:
        pass
    for tag, filt in _LZMA.items():
        try:
            cands.append(bytes([tag]) + lzma.compress(data, format=lzma.FORMAT_RAW, filters=filt))
        except Exception:
            pass
    for c in cands:
        if len(c) < len(best):
            best = c
    return best


def _unpack(blob):
    tag, payload = blob[0], blob[1:]
    if tag == 0:
        return payload
    if tag == 1:
        return zlib.decompress(payload)
    if tag == 2:
        return bz2.decompress(payload)
    if tag in _LZMA:
        return lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=_LZMA[tag])
    raise ValueError("unknown tag %d" % tag)


# ---------- range coder ----------
def _rc_encode(steps):
    low = 0
    rng = _TOP - 1
    cache = 0
    csize = 1
    out = bytearray()
    for cl, f, tot in steps:
        r = rng // tot
        low += r * cl
        rng = r * f
        while rng < _BOT:
            rng <<= 8
            if low < _HI or low >= _TOP:
                carry = low >> 64
                out.append((cache + carry) & 0xFF)
                if csize > 1:
                    out.extend(bytes([(0xFF + carry) & 0xFF]) * (csize - 1))
                csize = 0
                cache = (low >> 56) & 0xFF
            csize += 1
            low = (low & _M56) << 8
    for _ in range(9):
        if low < _HI or low >= _TOP:
            carry = low >> 64
            out.append((cache + carry) & 0xFF)
            if csize > 1:
                out.extend(bytes([(0xFF + carry) & 0xFF]) * (csize - 1))
            csize = 0
            cache = (low >> 56) & 0xFF
        csize += 1
        low = (low & _M56) << 8
    return bytes(out)


def _scale(counts):
    tot = sum(counts)
    if tot <= _LIM:
        return counts
    n = len(counts)
    if n > _LIM // 2:
        return None
    return [1 + c * (_LIM - n) // tot for c in counts]


# ---------- word model ----------
def _wm_compress(data):
    toks = _TOK.findall(data)
    n = len(toks)
    if n < 2:
        return None
    first = 1 if toks[0][:1].isalpha() else 0
    seq = []
    isw = bool(first)
    expect = True
    for t in toks:
        if isw:
            if t.islower():
                if expect:
                    seq.append(b"")
                seq.append(t)
            elif t[:1].isupper() and (len(t) == 1 or t[1:].islower()):
                if not expect:
                    seq.append(b"")
                seq.append(t.lower())
            else:
                seq.append(t)
        else:
            seq.append(t)
            expect = _SENT.search(t) is not None
        isw = not isw
    cnt = Counter(seq)
    wd = sorted((k for k in cnt if not k or k[:1].isalpha()), key=lambda k: (-cnt[k], k))
    sd = sorted((k for k in cnt if k and not k[:1].isalpha()), key=lambda k: (-cnt[k], k))
    wc = _scale([cnt[k] for k in wd])
    sc = _scale([cnt[k] for k in sd])
    if wc is None or sc is None:
        return None
    trip = {}
    for keys, counts in ((wd, wc), (sd, sc)):
        tot = sum(counts)
        cl = 0
        for k, c in zip(keys, counts):
            trip[k] = (cl, c, tot)
            cl += c
    rc = _rc_encode([trip[k] for k in seq])
    h = bytearray()
    _varint(n, h)
    h.append(first)
    _varint(len(wd), h)
    _varint(len(sd), h)
    for c in wc:
        _varint(c, h)
    for c in sc:
        _varint(c, h)
    for s in sd:
        _varint(len(s), h)
    h += b"".join(sd)
    h += b"\n".join(wd)
    hp = _pack(bytes(h))
    out = bytearray([32])
    _varint(len(hp), out)
    out += hp
    out += rc
    return bytes(out)


def _wm_decompress(payload):
    hl, pos = _getvar(payload, 0)
    h = _unpack(payload[pos:pos + hl])
    buf = payload[pos + hl:] + bytes(32)
    n, p = _getvar(h, 0)
    first = h[p]
    p += 1
    nw, p = _getvar(h, p)
    ns, p = _getvar(h, p)
    wc = []
    for _ in range(nw):
        c, p = _getvar(h, p)
        wc.append(c)
    sc = []
    for _ in range(ns):
        c, p = _getvar(h, p)
        sc.append(c)
    lens = []
    for _ in range(ns):
        c, p = _getvar(h, p)
        lens.append(c)
    sd = []
    for ln in lens:
        sd.append(h[p:p + ln])
        p += ln
    wd = h[p:].split(b"\n") if nw else []
    if len(wd) != nw:
        raise ValueError("corrupt word dictionary")
    wcum = [0] + list(accumulate(wc))
    scum = [0] + list(accumulate(sc))
    wtot = wcum[-1]
    stot = scum[-1]
    code = int.from_bytes(buf[:9], "big")
    bp = 9
    rng = _TOP - 1
    out = []
    isw = bool(first)
    expect = True
    for _ in range(n):
        if isw:
            flip = False
            while True:
                r = rng // wtot
                v = code // r
                if v >= wtot:
                    v = wtot - 1
                s = bisect_right(wcum, v) - 1
                code -= wcum[s] * r
                rng = r * wc[s]
                while rng < _BOT:
                    code = (code << 8) | buf[bp]
                    bp += 1
                    rng <<= 8
                key = wd[s]
                if key:
                    break
                flip = True
            if key.islower() and expect != flip:
                key = key[:1].upper() + key[1:]
            out.append(key)
        else:
            r = rng // stot
            v = code // r
            if v >= stot:
                v = stot - 1
            s = bisect_right(scum, v) - 1
            code -= scum[s] * r
            rng = r * sc[s]
            while rng < _BOT:
                code = (code << 8) | buf[bp]
                bp += 1
                rng <<= 8
            key = sd[s]
            out.append(key)
            expect = _SENT.search(key) is not None
        isw = not isw
    return b"".join(out)


# ---------- segmentation ----------
def _changepoint(data):
    """Position where the share of letters/spaces changes most sharply, or 0."""
    n = len(data)
    if n < 4096:
        return 0
    cls = data.translate(_CLS)
    T = sum(cls)
    best = 0.0
    bk = 0
    bd = 0
    k = 0
    for s in accumulate(cls):
        k += 1
        if k == n:
            break
        d = s * n - T * k
        sc = d * d / (k * (n - k))
        if sc > best:
            best = sc
            bk = k
            bd = d
    if bk < 1024 or n - bk < 1024:
        return 0
    if abs(bd) / (bk * (n - bk)) < 0.15:
        return 0
    return bk


def _nosplit(data):
    best = _pack(data)
    try:
        w = _wm_compress(data)
    except Exception:
        w = None
    if w is not None and len(w) < len(best) and _wm_decompress(w[1:]) == data:
        best = w
    return best


def compress(data: bytes) -> bytes:
    data = bytes(data)
    best = _nosplit(data)
    k = _changepoint(data)
    if k:
        a = _nosplit(data[:k])
        b = _nosplit(data[k:])
        cand = bytearray([33])
        _varint(len(a), cand)
        cand += a
        cand += b
        if len(cand) < len(best):
            best = bytes(cand)
    return best


def decompress(blob: bytes) -> bytes:
    blob = bytes(blob)
    if not blob:
        raise ValueError("empty input")
    tag = blob[0]
    if tag == 32:
        return _wm_decompress(blob[1:])
    if tag == 33:
        la, pos = _getvar(blob, 1)
        return decompress(blob[pos:pos + la]) + decompress(blob[pos + la:])
    return _unpack(blob)
