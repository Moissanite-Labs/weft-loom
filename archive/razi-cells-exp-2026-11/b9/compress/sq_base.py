import zlib, bz2, lzma, json

_F = [{'id': lzma.FILTER_LZMA2, 'preset': 9 | lzma.PRESET_EXTREME, 'lc': 4, 'lp': 0, 'pb': 0}]


def _vi(n, out):
    while n >= 0x80:
        out.append((n & 0x7f) | 0x80)
        n >>= 7
    out.append(n)


def _rvi(b, pos):
    n = 0
    s = 0
    while True:
        c = b[pos]
        pos += 1
        n |= (c & 0x7f) << s
        if c < 0x80:
            return n, pos
        s += 7


def _ser(obj, st, ss, si):
    t = type(obj)
    if t is dict:
        st.append(100)
        _vi(len(obj), st)
        for k, v in obj.items():
            if type(k) is not str:
                raise ValueError
            ss.append(k)
            _ser(v, st, ss, si)
    elif t is list:
        st.append(108)
        _vi(len(obj), st)
        for v in obj:
            _ser(v, st, ss, si)
    elif t is str:
        st.append(115)
        ss.append(obj)
    elif t is bool:
        st.append(116 if obj else 70)
    elif t is int:
        st.append(105)
        _vi((obj << 1) ^ (obj >> 63) if obj >= -(1 << 63) and obj < (1 << 63) else (obj << 1) if obj >= 0 else ((-obj) << 1) - 1, si) if False else _vi(obj * 2 if obj >= 0 else -obj * 2 - 1, si)
    elif t is float:
        st.append(102)
        ss.append(repr(obj))
    elif obj is None:
        st.append(110)
    else:
        raise ValueError


def _des(st, pos, strs, sp, ib, ip):
    c = st[pos]
    pos += 1
    if c == 100:
        n, pos = _rvi(st, pos)
        d = {}
        for _ in range(n):
            k = strs[sp]
            sp += 1
            d[k], pos, sp, ip = _des(st, pos, strs, sp, ib, ip)
        return d, pos, sp, ip
    if c == 108:
        n, pos = _rvi(st, pos)
        l = []
        for _ in range(n):
            v, pos, sp, ip = _des(st, pos, strs, sp, ib, ip)
            l.append(v)
        return l, pos, sp, ip
    if c == 115:
        return strs[sp], pos, sp + 1, ip
    if c == 116:
        return True, pos, sp, ip
    if c == 70:
        return False, pos, sp, ip
    if c == 105:
        z, ip = _rvi(ib, ip)
        return (z >> 1) if not (z & 1) else -((z + 1) >> 1), pos, sp, ip
    if c == 102:
        return float(strs[sp]), pos, sp + 1, ip
    if c == 110:
        return None, pos, sp, ip
    raise ValueError


_MODES = [dict(indent=2), dict(separators=(',', ':')), dict()]


def _json_payload(data):
    try:
        text = data.decode('utf-8')
        obj = json.loads(text)
    except Exception:
        return None
    mode = -1
    for i, kw in enumerate(_MODES):
        if json.dumps(obj, **kw) == text:
            mode = i
            break
    if mode < 0:
        return None
    st = bytearray()
    ss = []
    si = bytearray()
    try:
        _ser(obj, st, ss, si)
    except (ValueError, RecursionError):
        return None
    if any('\x00' in s for s in ss):
        return None
    sb = '\x00'.join(ss).encode('utf-8')
    out = bytearray([1 + mode])
    _vi(len(st), out)
    _vi(len(sb), out)
    out += st
    out += sb
    out += si
    return bytes(out)


def _unjson(p):
    mode = p[0] - 1
    lst, pos = _rvi(p, 1)
    lsb, pos = _rvi(p, pos)
    st = p[pos:pos + lst]
    pos += lst
    strs = p[pos:pos + lsb].decode('utf-8').split('\x00')
    ib = p[pos + lsb:]
    obj, _, _, _ = _des(st, 0, strs, 0, ib, 0)
    return json.dumps(obj, **_MODES[mode]).encode('utf-8')


def _cands(payload):
    yield b'\x00' + payload
    yield b'\x01' + zlib.compress(payload, 9)
    yield b'\x02' + bz2.compress(payload, 9)
    yield b'\x03' + lzma.compress(payload, format=lzma.FORMAT_RAW, filters=_F)


def compress(data: bytes) -> bytes:
    payloads = [b'\x00' + data]
    jp = _json_payload(data)
    if jp is not None:
        payloads.append(jp)
    return min((c for p in payloads for c in _cands(p)), key=len)


def decompress(blob: bytes) -> bytes:
    t, body = blob[0], blob[1:]
    if t == 0:
        p = body
    elif t == 1:
        p = zlib.decompress(body)
    elif t == 2:
        p = bz2.decompress(body)
    else:
        p = lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_F)
    if p[0] == 0:
        return p[1:]
    return _unjson(p)
