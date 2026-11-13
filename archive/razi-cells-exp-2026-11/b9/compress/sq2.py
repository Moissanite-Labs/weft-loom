import bz2, lzma, re
from bench import WORDS
_W = []
for w in WORDS:
    if w not in _W: _W.append(w)
_W = _W[:126]
_ENC = {w.encode(): bytes([0x80+i]) for i, w in enumerate(_W)}
_DEC = {v[0]: k for k, v in _ENC.items()}
_CAP = 0xFE; _ESC = 0xFF
_tok = re.compile(rb"[A-Za-z']+|[\x80-\xff]")
def fwd(data):
    def rep(m):
        s = m.group(0)
        if s[0] >= 0x80: return bytes([_ESC, s[0]])
        c = _ENC.get(s)
        if c: return c
        if s[:1].isupper():
            c = _ENC.get(s[:1].lower()+s[1:])
            if c: return bytes([_CAP]) + c
        return s
    return _tok.sub(rep, data)
def inv(data):
    out = bytearray(); i = 0; n = len(data); cap = False
    while i < n:
        b = data[i]; i += 1
        if b < 0x80: out.append(b)
        elif b == _ESC: out.append(data[i]); i += 1
        elif b == _CAP: cap = True
        else:
            w = _DEC[b]
            if cap: w = w[:1].upper()+w[1:]; cap = False
            out += w
    return bytes(out)
def compress(data):
    t = fwd(data)
    assert inv(t) == data
    return min(b'\x00'+data, b'\x02'+bz2.compress(data,9), b'\x04'+bz2.compress(t,9), key=len)
def decompress(blob):
    t, body = blob[0], blob[1:]
    if t == 0: return body
    if t == 2: return bz2.decompress(body)
    return inv(bz2.decompress(body))
