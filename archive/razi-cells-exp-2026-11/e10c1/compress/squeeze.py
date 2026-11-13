import lzma, bz2, zlib, re, json

_WORDS = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split()
          + ["compression","algorithm","dictionary","entropy","sentence","paragraph","function","variable","network","system","quickly","because","however","therefore","between","another","through","example","language","python"])
_FRAGS = ['"id": ', '"name": "', '"email": "', '"active": ', '"score": ', '"tags": [', '"address": {', '"city": "', '"zip": "', '@example.com', 'true', 'false']
_TOKS = _FRAGS + _WORDS
assert len(_TOKS) <= 127
_IDX = {t: i + 0x81 for i, t in enumerate(_TOKS)}
_RE = re.compile("|".join(re.escape(f) for f in _FRAGS) + r"|[A-Za-z]+")

_FILTS = [[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": lc, "lp": 0, "pb": 0, "mf": lzma.MF_BT4, "nice_len": 273, "depth": 0}] for lc in (0, 1, 2, 3, 4)]


def _tok(s):
    out = bytearray()
    pos = 0
    for m in _RE.finditer(s):
        w = m.group()
        i = _IDX.get(w)
        cap = False
        if i is None:
            lw = w.lower()
            if w == lw.capitalize():
                i = _IDX.get(lw)
                cap = i is not None
        if i is None:
            continue
        gap = s[pos:m.start()]
        if gap.endswith(" "):
            out += gap[:-1].encode("ascii")
        else:
            out += gap.encode("ascii")
            out.append(0x7F)
        if cap:
            out.append(0x80)
        out.append(i)
        pos = m.end()
    out += s[pos:].encode("ascii")
    return bytes(out)


def _detok(b):
    out = bytearray()
    cap = False
    nosp = False
    for c in b:
        if c == 0x7F:
            nosp = True
        elif c < 0x80:
            out.append(c)
        elif c == 0x80:
            cap = True
        else:
            t = _TOKS[c - 0x81]
            if cap:
                t = t.capitalize()
                cap = False
            if not nosp:
                out.append(0x20)
            nosp = False
            out += t.encode("ascii")
    return bytes(out)


def _flatten(recs):
    keys = list(recs[0].keys())
    for r in recs:
        if not isinstance(r, dict) or list(r.keys()) != keys:
            return None
    sch = {}
    lines = []
    for k in keys:
        vals = [r[k] for r in recs]
        sub = None
        if all(isinstance(v, dict) and v for v in vals):
            sub = _flatten(vals)
        if sub is not None:
            sch[k] = sub[0]
            lines += sub[1]
        else:
            sch[k] = None
            lines.extend(json.dumps(v) for v in vals)
    return sch, lines


def _unflatten(sch, lines, n, pos):
    recs = [{} for _ in range(n)]
    for k, sub in sch.items():
        if sub is None:
            for i in range(n):
                recs[i][k] = json.loads(lines[pos + i])
            pos += n
        else:
            subrecs, pos = _unflatten(sub, lines, n, pos)
            for i in range(n):
                recs[i][k] = subrecs[i]
    return recs, pos


def _columnar(data):
    try:
        obj = json.loads(data)
    except Exception:
        return None
    if not isinstance(obj, list) or not obj or not all(isinstance(r, dict) for r in obj):
        return None
    if json.dumps(obj, indent=2).encode() != data:
        return None
    fl = _flatten(obj)
    if fl is None:
        return None
    sch, lines = fl
    payload = json.dumps(sch) + "\n" + str(len(obj)) + "\n" + "\n".join(lines)
    return _tok(payload)


def _uncolumnar(t):
    s = _detok(t).decode("ascii")
    a, b, rest = s.split("\n", 2)
    sch = json.loads(a)
    n = int(b)
    lines = rest.split("\n") if rest else []
    recs, _ = _unflatten(sch, lines, n, 0)
    return json.dumps(recs, indent=2).encode()


def compress(data: bytes) -> bytes:
    cands = [b"\x00" + data, b"\x02" + bz2.compress(data, 9), b"\x03" + zlib.compress(data, 9)]
    for k, f in enumerate(_FILTS):
        cands.append(bytes([0x10 + k]) + lzma.compress(data, format=lzma.FORMAT_RAW, filters=f))
    if data.isascii():
        t = _tok(data.decode("ascii"))
        if _detok(t) == data:
            for k, f in enumerate(_FILTS):
                cands.append(bytes([0x20 + k]) + lzma.compress(t, format=lzma.FORMAT_RAW, filters=f))
        c = _columnar(data)
        if c is not None:
            try:
                ok = _uncolumnar(c) == data
            except Exception:
                ok = False
            if ok:
                for k, f in enumerate(_FILTS):
                    cands.append(bytes([0x30 + k]) + lzma.compress(c, format=lzma.FORMAT_RAW, filters=f))
    return min(cands, key=len)


def decompress(blob: bytes) -> bytes:
    tag, body = blob[0], blob[1:]
    if tag == 0:
        return body
    if tag == 2:
        return bz2.decompress(body)
    if tag == 3:
        return zlib.decompress(body)
    if 0x10 <= tag < 0x20:
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_FILTS[tag - 0x10])
    if 0x20 <= tag < 0x30:
        return _detok(lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_FILTS[tag - 0x20]))
    if 0x30 <= tag < 0x40:
        return _uncolumnar(lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_FILTS[tag - 0x30]))
    raise ValueError("bad tag")
