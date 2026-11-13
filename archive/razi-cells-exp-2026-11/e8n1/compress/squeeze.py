import json
import lzma
import re
from collections import Counter

_LZMA_FILTERS_COMP = [
    {
        "id": lzma.FILTER_LZMA1,
        "preset": 9 | lzma.PRESET_EXTREME,
        "lc": 3,
        "lp": 0,
        "pb": 0,
        "nice_len": 273,
    }
]
_LZMA_FILTERS_DECOMP = [
    {
        "id": lzma.FILTER_LZMA1,
        "lc": 3,
        "lp": 0,
        "pb": 0,
    }
]

_WORD_RE = re.compile(r"[A-Za-z]{2,}")


def _to_columnar(o):
    if isinstance(o, dict):
        return {k: _to_columnar(v) for k, v in o.items()}
    if isinstance(o, list):
        if (
            len(o) > 1
            and all(isinstance(x, dict) for x in o)
            and len({tuple(x.keys()) for x in o}) == 1
            and "__col__" not in o[0]
        ):
            keys = list(o[0].keys())
            cols = {k: _to_columnar([x[k] for x in o]) for k in keys}
            return {"__col__": keys, "d": cols, "n": len(o)}
        return [_to_columnar(x) for x in o]
    return o


def _from_columnar(o):
    if isinstance(o, dict):
        if "__col__" in o and "d" in o and "n" in o and len(o) == 3:
            keys = o["__col__"]
            n = o["n"]
            cols = {k: _from_columnar(v) for k, v in o["d"].items()}
            return [{k: cols[k][i] for k in keys} for i in range(n)]
        return {k: _from_columnar(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_from_columnar(x) for x in o]
    return o


def _transform_json_section(s: str):
    sep = "\n---JSON_SECTION---\n"
    if sep in s:
        prefix, json_part = s.split(sep, 1)
        try:
            obj = json.loads(json_part)
            if json.dumps(obj, indent=2) == json_part:
                col_obj = _to_columnar(obj)
                compact_json = json.dumps(col_obj, separators=(",", ":"))
                return True, prefix + sep + compact_json
        except Exception:
            pass
    else:
        try:
            obj = json.loads(s)
            if json.dumps(obj, indent=2) == s:
                col_obj = _to_columnar(obj)
                compact_json = json.dumps(col_obj, separators=(",", ":"))
                return True, compact_json
        except Exception:
            pass
    return False, s


def _untransform_json_section(s: str, has_sep: bool) -> str:
    sep = "\n---JSON_SECTION---\n"
    if has_sep:
        prefix, compact_json = s.split(sep, 1)
        col_obj = json.loads(compact_json)
        obj = _from_columnar(col_obj)
        return prefix + sep + json.dumps(obj, indent=2)
    else:
        col_obj = json.loads(s)
        obj = _from_columnar(col_obj)
        return json.dumps(obj, indent=2)


def _encode_words(s: str):
    raw_bytes = s.encode("utf-8")
    if any(b >= 128 for b in raw_bytes):
        return None
    words = _WORD_RE.findall(s)
    if len(words) < 20:
        return None
    counts = Counter(w.lower() for w in words)
    # Use bytes 128..253 (126 slots) for single-byte word tokens,
    # and byte 254 as Capitalize Next Word prefix.
    vocab = [w for w, c in counts.most_common(126) if c > 2]
    if not vocab:
        return None
    word_to_id = {w: 128 + i for i, w in enumerate(vocab)}

    out = bytearray()
    last = 0
    for m in _WORD_RE.finditer(s):
        start, end = m.span()
        if start > last:
            out.extend(s[last:start].encode("ascii"))
        w = m.group(0)
        lw = w.lower()
        idx = word_to_id.get(lw)
        if idx is not None:
            if w == lw:
                out.append(idx)
            elif len(w) > 1 and w[0].isupper() and w[1:] == lw[1:]:
                out.append(254)
                out.append(idx)
            else:
                out.extend(w.encode("ascii"))
        else:
            out.extend(w.encode("ascii"))
        last = end
    if last < len(s):
        out.extend(s[last:].encode("ascii"))

    header = " ".join(vocab).encode("ascii") + b"\x00"
    return header + bytes(out)


def _decode_words(b: bytes) -> str:
    sep_idx = b.index(b"\x00")
    vocab_str = b[:sep_idx].decode("ascii")
    vocab = vocab_str.split(" ") if vocab_str else []
    body = b[sep_idx + 1 :]

    res = []
    i = 0
    n = len(body)
    while i < n:
        byte = body[i]
        if byte == 254 and i + 1 < n and 128 <= body[i + 1] < 128 + len(vocab):
            w = vocab[body[i + 1] - 128]
            res.append(w[0].upper() + w[1:])
            i += 2
        elif 128 <= byte < 128 + len(vocab):
            res.append(vocab[byte - 128])
            i += 1
        else:
            start = i
            while i < n and body[i] < 128:
                i += 1
            res.append(body[start:i].decode("ascii"))
    return "".join(res)


def compress(data: bytes) -> bytes:
    if not data:
        return b""

    candidates = [
        b"\x00"
        + lzma.compress(data, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS_COMP)
    ]

    try:
        s = data.decode("utf-8")
        has_sep = "\n---JSON_SECTION---\n" in s
        json_ok, s_trans = _transform_json_section(s)
        encoded = _encode_words(s_trans)
        if encoded is not None:
            mode = (2 if json_ok else 0) | (4 if has_sep else 0) | 1
            c_enc = bytes([mode]) + lzma.compress(
                encoded, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS_COMP
            )
            if decompress(c_enc) == data:
                candidates.append(c_enc)
        elif json_ok:
            mode = 2 | (4 if has_sep else 0)
            c_json = bytes([mode]) + lzma.compress(
                s_trans.encode("utf-8"),
                format=lzma.FORMAT_RAW,
                filters=_LZMA_FILTERS_COMP,
            )
            if decompress(c_json) == data:
                candidates.append(c_json)
    except Exception:
        pass

    return min(candidates, key=len)


def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    mode = data[0]
    raw = lzma.decompress(
        data[1:], format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS_DECOMP
    )
    if mode == 0:
        return raw

    if mode & 1:
        s = _decode_words(raw)
    else:
        s = raw.decode("utf-8")

    if mode & 2:
        has_sep = bool(mode & 4)
        s = _untransform_json_section(s, has_sep)

    return s.encode("utf-8")
