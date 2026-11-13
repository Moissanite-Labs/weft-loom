import lzma, zlib, bz2, re, struct

_LZMA_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME,
                  "lc": 4, "lp": 0, "pb": 0, "nice_len": 273, "mf": lzma.MF_BT4, "depth": 0}]

PREC = 62
FULL = 1 << PREC
HALF = FULL >> 1
QUARTER = FULL >> 2
INC = 32
LIMIT = 1 << 24
_TOK = re.compile(rb"[A-Za-z]+|[^A-Za-z]+")
_DIG = re.compile(rb"[0-9]")


class Model:
    def __init__(self, n):
        self.n = n
        self.cnt = [1] * n
        self.tot = n
        self.log = 1
        while self.log * 2 <= n:
            self.log *= 2
        self._build()

    def _build(self):
        n = self.n
        t = [0] * (n + 1)
        cnt = self.cnt
        for i in range(1, n + 1):
            t[i] += cnt[i - 1]
            j = i + (i & -i)
            if j <= n:
                t[j] += t[i]
        self.tree = t

    def cum(self, i):
        r = 0
        t = self.tree
        while i > 0:
            r += t[i]
            i -= i & -i
        return r

    def find(self, target):
        pos = 0
        bm = self.log
        t = self.tree
        n = self.n
        while bm:
            np_ = pos + bm
            if np_ <= n and t[np_] <= target:
                target -= t[np_]
                pos = np_
            bm >>= 1
        return pos, target

    def update(self, sym):
        self.cnt[sym] += INC
        self.tot += INC
        i = sym + 1
        t = self.tree
        n = self.n
        while i <= n:
            t[i] += INC
            i += i & -i
        if self.tot > LIMIT:
            self.cnt = [(c + 1) >> 1 for c in self.cnt]
            self.tot = sum(self.cnt)
            self._build()


class Enc:
    def __init__(self):
        self.low = 0
        self.high = FULL - 1
        self.pend = 0
        self.out = bytearray()
        self.bits = 0
        self.nb = 0

    def bit(self, b):
        self.bits = (self.bits << 1) | b
        self.nb += 1
        if self.nb == 8:
            self.out.append(self.bits)
            self.bits = 0
            self.nb = 0

    def bitp(self, b):
        self.bit(b)
        while self.pend:
            self.bit(1 - b)
            self.pend -= 1

    def encode(self, lo, hi, tot):
        r = self.high - self.low + 1
        self.high = self.low + (r * hi) // tot - 1
        self.low = self.low + (r * lo) // tot
        while True:
            if self.high < HALF:
                self.bitp(0)
            elif self.low >= HALF:
                self.bitp(1)
                self.low -= HALF
                self.high -= HALF
            elif self.low >= QUARTER and self.high < HALF + QUARTER:
                self.pend += 1
                self.low -= QUARTER
                self.high -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def finish(self):
        self.pend += 1
        self.bitp(0 if self.low < QUARTER else 1)
        while self.nb:
            self.bit(0)
        return bytes(self.out)


class Dec:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.low = 0
        self.high = FULL - 1
        self.val = 0
        for _ in range(PREC):
            self.val = (self.val << 1) | self.getbit()

    def getbit(self):
        i = self.pos >> 3
        if i < len(self.data):
            b = (self.data[i] >> (7 - (self.pos & 7))) & 1
        else:
            b = 0
        self.pos += 1
        return b

    def target(self, tot):
        r = self.high - self.low + 1
        return ((self.val - self.low + 1) * tot - 1) // r

    def decode(self, lo, hi, tot):
        r = self.high - self.low + 1
        self.high = self.low + (r * hi) // tot - 1
        self.low = self.low + (r * lo) // tot
        while True:
            if self.high < HALF:
                pass
            elif self.low >= HALF:
                self.low -= HALF
                self.high -= HALF
                self.val -= HALF
            elif self.low >= QUARTER and self.high < HALF + QUARTER:
                self.low -= QUARTER
                self.high -= QUARTER
                self.val -= QUARTER
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.val = (self.val << 1) | self.getbit()


def _ctx(nonword):
    return _DIG.sub(b"", nonword)[-12:]


def _best_lz(data):
    c = [b"\x01" + lzma.compress(data, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS),
         b"\x02" + bz2.compress(data, 9), b"\x03" + zlib.compress(data, 9), b"\x00" + data]
    return min(c, key=len)


def _unlz(blob):
    tag, body = blob[:1], blob[1:]
    if tag == b"\x01":
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)
    if tag == b"\x02":
        return bz2.decompress(body)
    if tag == b"\x03":
        return zlib.decompress(body)
    return body


def _word_compress(data):
    toks = _TOK.findall(data)
    if not toks:
        return None
    first_word = 1 if toks[0][:1].isalpha() else 0
    words = toks[first_word::2]
    nonwords = toks[1 - first_word::2]
    vocab = {}
    ids = []
    order = []
    for w in words:
        i = vocab.get(w)
        if i is None:
            i = vocab[w] = len(order)
            order.append(w)
        ids.append(i)
    V = len(order)
    if V == 0:
        return None
    enc = Enc()
    models = {}
    # context for word k is nonword preceding it
    for k, sym in enumerate(ids):
        if first_word:
            ctx = _ctx(nonwords[k - 1]) if k > 0 else b""
        else:
            ctx = _ctx(nonwords[k])
        m = models.get(ctx)
        if m is None:
            m = models[ctx] = Model(V)
        lo = m.cum(sym)
        enc.encode(lo, lo + m.cnt[sym], m.tot)
        m.update(sym)
    ac = enc.finish()
    dblob = _best_lz(b"\n".join(order))
    rblob = _best_lz(b"A".join(nonwords))
    hdr = struct.pack("<BIIII", first_word, V, len(ids), len(dblob), len(rblob))
    return b"\x04" + hdr + dblob + rblob + ac


def _word_decompress(body):
    first_word, V, nids, ld, lr = struct.unpack("<BIIII", body[:17])
    p = 17
    order = _unlz(body[p:p + ld]).split(b"\n") if ld else []
    p += ld
    nonwords = _unlz(body[p:p + lr]).split(b"A")
    p += lr
    dec = Dec(body[p:])
    models = {}
    out = []
    for k in range(nids):
        if first_word:
            ctx = _ctx(nonwords[k - 1]) if k > 0 else b""
        else:
            ctx = _ctx(nonwords[k])
        m = models.get(ctx)
        if m is None:
            m = models[ctx] = Model(V)
        t = dec.target(m.tot)
        sym, rem = m.find(t)
        lo = t - rem
        dec.decode(lo, lo + m.cnt[sym], m.tot)
        m.update(sym)
        out.append(order[sym])
    # interleave
    res = []
    if first_word:
        for k in range(nids):
            res.append(out[k])
            if k < len(nonwords):
                res.append(nonwords[k])
        # trailing nonword if any
        if len(nonwords) > nids:
            res.extend(nonwords[nids:])
    else:
        for k in range(nids):
            res.append(nonwords[k])
            res.append(out[k])
        if len(nonwords) > nids:
            res.extend(nonwords[nids:])
    return b"".join(res)


def compress(data: bytes) -> bytes:
    cands = [_best_lz(data)]
    try:
        w = _word_compress(data)
        if w is not None:
            cands.append(w)
    except Exception:
        pass
    return min(cands, key=len)


def decompress(blob: bytes) -> bytes:
    if blob[:1] == b"\x04":
        return _word_decompress(blob[1:])
    return _unlz(blob)


# --- JSON canonicalization stage: strip indent=2 pretty-printing reversibly ---
import json as _json

def _json_compress(data):
    try:
        obj = _json.loads(data)
    except Exception:
        return None
    if _json.dumps(obj, indent=2).encode() != data:
        return None
    compact = _json.dumps(obj, separators=(",", ":")).encode()
    return b"\x05" + _best_lz(compact)


_old_compress = compress
_old_decompress = decompress


def compress(data: bytes) -> bytes:
    cands = [_old_compress(data)]
    j = _json_compress(data)
    if j is not None:
        cands.append(j)
    return min(cands, key=len)


def decompress(blob: bytes) -> bytes:
    if blob[:1] == b"\x05":
        return _json.dumps(_json.loads(_unlz(blob[1:])), indent=2).encode()
    return _old_decompress(blob)
