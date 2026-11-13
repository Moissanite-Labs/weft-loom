"""squeeze: stdlib-only compressor. compress(bytes)->bytes, decompress(bytes)->bytes.

Format: 1 tag byte + payload. The smallest candidate wins.
  0 = stored, 1 = zlib, 2 = bz2, 3 = lzma raw (LZMA2, tuned for text)
  4 = token PPM: the input is split into alternating alphanumeric and
      non-alphanumeric tokens; each token is coded with an adaptive
      PPM-style model (context = previous tokens, escape to lower orders,
      finally spelled byte by byte) driven by a 64-bit range coder.
      Nothing is assumed about the input: the model learns everything.
"""
import bz2
import lzma
import re
import zlib

_LZMA_FILTERS = [{
    "id": lzma.FILTER_LZMA2,
    "preset": 9 | lzma.PRESET_EXTREME,
    "dict_size": 1 << 26,
    "lc": 4, "lp": 0, "pb": 0,
    "nice_len": 273,
    "mf": lzma.MF_BT4,
    "depth": 1000,
}]

_TOK = re.compile(rb"[A-Za-z0-9]+|[^A-Za-z0-9]+")
_ALNUM = re.compile(rb"[A-Za-z0-9]")
_MASK = (1 << 64) - 1
_TOP = 1 << 56
_BOT = 1 << 48
_LIMIT = 1 << 24
_INC = 24
_COMBOS = [(1, 0), (2, 2)]      # (word order, separator order) tried in turn
_MAX_TOKEN_INPUT = 16 << 20


class _Enc:
    def __init__(self):
        self.low = 0
        self.rng = _MASK
        self.out = bytearray()

    def encode(self, cum, freq, tot):
        r = self.rng // tot
        low = self.low + cum * r
        rng = r * freq
        out = self.out
        while True:
            if (low ^ (low + rng - 1)) >= _TOP:
                if rng >= _BOT:
                    break
                rng = (-low) & (_BOT - 1)
            out.append(low >> 56)
            low = (low << 8) & _MASK
            rng <<= 8
        self.low = low
        self.rng = rng

    def finish(self):
        self.out += self.low.to_bytes(8, "big")
        return bytes(self.out)


class _Dec:
    def __init__(self, buf, pos):
        self.buf = buf
        self.n = len(buf)
        self.code = int.from_bytes(buf[pos:pos + 8].ljust(8, b"\0"), "big")
        self.pos = pos + 8
        self.low = 0
        self.rng = _MASK
        self.r = 1

    def target(self, tot):
        self.r = self.rng // tot
        return (self.code - self.low) // self.r

    def update(self, cum, freq):
        r = self.r
        low = self.low + cum * r
        rng = r * freq
        code = self.code
        buf = self.buf
        pos = self.pos
        n = self.n
        while True:
            if (low ^ (low + rng - 1)) >= _TOP:
                if rng >= _BOT:
                    break
                rng = (-low) & (_BOT - 1)
            code = ((code << 8) & _MASK) | (buf[pos] if pos < n else 0)
            pos += 1
            low = (low << 8) & _MASK
            rng <<= 8
        self.low = low
        self.rng = rng
        self.code = code
        self.pos = pos


class _Ctx:
    __slots__ = ("syms", "counts", "index", "total")

    def __init__(self):
        self.syms = []
        self.counts = []
        self.index = {}
        self.total = 0

    def add(self, sym):
        self.index[sym] = len(self.syms)
        self.syms.append(sym)
        self.counts.append(1)
        self.total += 1

    def bump(self, idx):
        self.counts[idx] += 2
        self.total += 2
        if self.total > _LIMIT:
            self.counts[:] = [(c + 1) >> 1 for c in self.counts]
            self.total = sum(self.counts)


def _find(counts, t):
    acc = 0
    for i, c in enumerate(counts):
        acc += c
        if t < acc:
            return i, acc - c
    raise ValueError("corrupt stream")


def _tok_compress(data, ow, os_):
    toks = _TOK.findall(data)
    n = len(toks)
    if n == 0 or n >= (1 << 32):
        return None
    first = 1 if _ALNUM.match(toks[0]) else 0
    enc = _Enc()
    encode = enc.encode
    tabs = ({}, {}, {}, {})
    chars = [[1] * 257, [1] * 257]
    ctot = [257, 257]
    orders = (os_, ow)
    p1 = p2 = p3 = b""
    typ = first
    for tok in toks:
        keys = (typ, p1, (p2, p1), (p3, p2, p1))
        k = orders[typ]
        while k >= 0:
            tab = tabs[k]
            key = keys[k]
            m = tab.get(key)
            if m is None:
                m = tab[key] = _Ctx()
                m.add(tok)
            else:
                idx = m.index.get(tok)
                counts = m.counts
                if idx is None:
                    d = len(counts)
                    encode(m.total, d, m.total + d)
                    m.add(tok)
                else:
                    encode(sum(counts[:idx]), counts[idx], m.total + len(counts))
                    m.bump(idx)
                    break
            k -= 1
        else:
            cnt = chars[typ]
            tot = ctot[typ]
            for b in tok:
                encode(sum(cnt[:b]), cnt[b], tot)
                cnt[b] += _INC
                tot += _INC
            encode(sum(cnt[:256]), cnt[256], tot)
            cnt[256] += _INC
            tot += _INC
            if tot > _LIMIT:
                cnt[:] = [(c + 1) >> 1 for c in cnt]
                tot = sum(cnt)
            ctot[typ] = tot
        p3, p2, p1 = p2, p1, tok
        typ ^= 1
    head = bytes([4, ow | (os_ << 2) | (first << 4)]) + n.to_bytes(4, "big")
    return head + enc.finish()


def _tok_decompress(blob):
    flags = blob[1]
    ow = flags & 3
    os_ = (flags >> 2) & 3
    typ = (flags >> 4) & 1
    n = int.from_bytes(blob[2:6], "big")
    dec = _Dec(blob, 6)
    target = dec.target
    update = dec.update
    tabs = ({}, {}, {}, {})
    chars = [[1] * 257, [1] * 257]
    ctot = [257, 257]
    orders = (os_, ow)
    p1 = p2 = p3 = b""
    out = []
    for _ in range(n):
        keys = (typ, p1, (p2, p1), (p3, p2, p1))
        k = orders[typ]
        pending = []
        while k >= 0:
            tab = tabs[k]
            key = keys[k]
            m = tab.get(key)
            if m is None:
                m = tab[key] = _Ctx()
                pending.append(m)
            else:
                counts = m.counts
                total = m.total
                d = len(counts)
                t = target(total + d)
                if t >= total:
                    update(total, d)
                    pending.append(m)
                else:
                    idx, cum = _find(counts, t)
                    update(cum, counts[idx])
                    tok = m.syms[idx]
                    m.bump(idx)
                    break
            k -= 1
        else:
            cnt = chars[typ]
            tot = ctot[typ]
            bs = bytearray()
            while True:
                t = target(tot)
                b, cum = _find(cnt, t)
                update(cum, cnt[b])
                cnt[b] += _INC
                tot += _INC
                if b == 256:
                    break
                bs.append(b)
            if tot > _LIMIT:
                cnt[:] = [(c + 1) >> 1 for c in cnt]
                tot = sum(cnt)
            ctot[typ] = tot
            tok = bytes(bs)
        for m in pending:
            m.add(tok)
        out.append(tok)
        p3, p2, p1 = p2, p1, tok
        typ ^= 1
    return b"".join(out)


def compress(data: bytes) -> bytes:
    data = bytes(data)
    cands = [b"\x00" + data]
    try:
        cands.append(b"\x01" + zlib.compress(data, 9))
    except Exception:
        pass
    try:
        cands.append(b"\x02" + bz2.compress(data, 9))
    except Exception:
        pass
    try:
        cands.append(b"\x03" + lzma.compress(data, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS))
    except Exception:
        pass
    if 32 <= len(data) <= _MAX_TOKEN_INPUT:
        for ow, os_ in _COMBOS:
            try:
                c = _tok_compress(data, ow, os_)
                if c is not None:
                    cands.append(c)
            except Exception:
                pass
    cands.sort(key=len)
    for c in cands:
        if c[0] == 4:
            # the custom coder is verified before it is trusted
            try:
                if _tok_decompress(c) != data:
                    continue
            except Exception:
                continue
        return c
    return b"\x00" + data


def decompress(blob: bytes) -> bytes:
    blob = bytes(blob)
    if not blob:
        raise ValueError("empty input")
    tag, body = blob[0], blob[1:]
    if tag == 0:
        return body
    if tag == 1:
        return zlib.decompress(body)
    if tag == 2:
        return bz2.decompress(body)
    if tag == 3:
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)
    if tag == 4:
        return _tok_decompress(blob)
    raise ValueError("unknown tag %d" % tag)
