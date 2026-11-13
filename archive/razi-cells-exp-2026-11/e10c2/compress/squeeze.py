import lzma, zlib, bz2, json

_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0}]


def _lz(b):
    return lzma.compress(b, format=lzma.FORMAT_RAW, filters=_FILTERS)


def _unlz(b):
    return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=_FILTERS)


def _paths(rec, prefix=()):
    out = []
    for k, v in rec.items():
        if isinstance(v, dict) and v:
            out.extend(_paths(v, prefix + (k,)))
        else:
            out.append(prefix + (k,))
    return out


def _get(rec, path):
    for k in path:
        rec = rec[k]
    return rec


def _set(rec, path, val):
    for k in path[:-1]:
        rec = rec.setdefault(k, {})
    rec[path[-1]] = val


def _columnar(data):
    try:
        s = data.decode("utf-8")
    except Exception:
        return None
    recs = None
    fmt = None
    try:
        obj = json.loads(s)
        if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
            if json.dumps(obj, indent=2) == s:
                recs, fmt = obj, 1
            elif json.dumps(obj) == s:
                recs, fmt = obj, 2
    except Exception:
        pass
    if recs is None:
        try:
            lines = s.split("\n")
            objs = [json.loads(l) for l in lines]
            if objs and all(isinstance(x, dict) for x in objs) and "\n".join(json.dumps(x) for x in objs) == s:
                recs, fmt = objs, 3
        except Exception:
            pass
    if recs is None:
        return None
    paths = _paths(recs[0])
    try:
        for r in recs:
            if _paths(r) != paths:
                return None
    except Exception:
        return None
    cols = []
    for p in paths:
        vals = [json.dumps(_get(r, p)) for r in recs]
        cols.append("\n".join(vals))
    header = json.dumps([fmt, len(recs), [list(p) for p in paths]])
    body = "\x00".join([header] + cols)
    return body.encode("utf-8")


def _uncolumnar(body):
    parts = body.decode("utf-8").split("\x00")
    fmt, n, paths = json.loads(parts[0])
    cols = [c.split("\n") for c in parts[1:]]
    recs = []
    for i in range(n):
        r = {}
        for p, c in zip(paths, cols):
            _set(r, p, json.loads(c[i]))
        recs.append(r)
    if fmt == 1:
        return json.dumps(recs, indent=2).encode("utf-8")
    if fmt == 2:
        return json.dumps(recs).encode("utf-8")
    return "\n".join(json.dumps(x) for x in recs).encode("utf-8")


def _best(p):
    cands = [b"\x00" + p, b"\x03" + bz2.compress(p, 9), b"\x02" + zlib.compress(p, 9)]
    try:
        cands.append(b"\x01" + _lz(p))
    except Exception:
        pass
    return min(cands, key=len)


def _unbest(b):
    t, body = b[:1], b[1:]
    if t == b"\x01":
        return _unlz(body)
    if t == b"\x02":
        return zlib.decompress(body)
    if t == b"\x03":
        return bz2.decompress(body)
    return body


def _multi(col):
    out = []
    for p in col.split(b"\x00"):
        b = _best(p)
        out.append(len(b).to_bytes(4, "big") + b)
    return b"".join(out)


def _unmulti(b):
    parts = []
    i = 0
    while i < len(b):
        n = int.from_bytes(b[i:i + 4], "big")
        parts.append(_unbest(b[i + 4:i + 4 + n]))
        i += 4 + n
    return b"\x00".join(parts)


def compress(data: bytes) -> bytes:
    cands = []
    try:
        cands.append(b"\x01" + _lz(data))
    except Exception:
        pass
    try:
        col = _columnar(data)
        if col is not None and _uncolumnar(col) == data:
            cands.append(b"\x04" + _lz(col))
            cands.append(b"\x05" + bz2.compress(col, 9))
            m = _multi(col)
            if _unmulti(m) == col:
                cands.append(b"\x06" + m)
    except Exception:
        pass
    cands.append(b"\x02" + zlib.compress(data, 9))
    cands.append(b"\x03" + bz2.compress(data, 9))
    cands.append(b"\x00" + data)
    return min(cands, key=len)


def decompress(blob: bytes) -> bytes:
    tag, body = blob[:1], blob[1:]
    if tag == b"\x01":
        return _unlz(body)
    if tag == b"\x04":
        return _uncolumnar(_unlz(body))
    if tag == b"\x05":
        return _uncolumnar(bz2.decompress(body))
    if tag == b"\x06":
        return _uncolumnar(_unmulti(body))
    if tag == b"\x02":
        return zlib.decompress(body)
    if tag == b"\x03":
        return bz2.decompress(body)
    return body
