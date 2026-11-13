import collections
import json
import lzma
import re

FILTERS = [
    {
        "id": lzma.FILTER_LZMA1,
        "preset": 9 | lzma.PRESET_EXTREME,
        "lc": 3,
        "lp": 0,
        "pb": 0,
        "nice_len": 273,
    }
]

WORD_RE = re.compile(rb"[A-Za-z]{2,}")


def _col_pack(obj):
    if isinstance(obj, dict):
        return {k: _col_pack(v) for k, v in obj.items()}
    if isinstance(obj, list):
        if (
            len(obj) > 1
            and all(isinstance(x, dict) for x in obj)
            and len({tuple(x.keys()) for x in obj}) == 1
        ):
            keys = list(obj[0].keys())
            cols = {k: _col_pack([x[k] for x in obj]) for k in keys}
            # Split structured string columns like "user-1234-word" or ISO dates
            for k, v in list(cols.items()):
                if isinstance(v, list) and all(isinstance(s, str) for s in v):
                    if all("-" in s for s in v):
                        parts = [s.split("-") for s in v]
                        if len({len(p) for p in parts}) == 1:
                            cols[k] = {"__split__": "-", "cols": [list(c) for c in zip(*parts)]}
            return {"__col__": keys, "d": cols, "n": len(obj)}
        return [_col_pack(x) for x in obj]
    return obj


def _col_unpack(obj):
    if isinstance(obj, dict):
        if "__col__" in obj and "d" in obj and "n" in obj:
            keys = obj["__col__"]
            n = obj["n"]
            cols = {}
            for k in keys:
                v = obj["d"][k]
                if isinstance(v, dict) and "__split__" in v:
                    sep = v["__split__"]
                    scols = v["cols"]
                    cols[k] = [sep.join( parts ) for parts in zip(*scols)]
                else:
                    cols[k] = _col_unpack(v)
            return [{k: cols[k][i] for k in keys} for i in range(n)]
        return {k: _col_unpack(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_col_unpack(x) for x in obj]
    return obj


def _try_json_encode(raw_bytes: bytes):
    # Find JSON start if present
    idx = raw_bytes.find(b"{\n")
    if idx == -1:
        return None
    prefix = raw_bytes[:idx]
    jsn_bytes = raw_bytes[idx:]
    try:
        jsn_str = jsn_bytes.decode("utf-8")
        parsed = json.loads(jsn_str)
        reconstructed = json.dumps(parsed, indent=2).encode("utf-8")
        if reconstructed != jsn_bytes:
            return None
        packed_obj = _col_pack(parsed)
        packed_jsn = json.dumps(packed_obj, separators=(",", ":")).encode("utf-8")
        return prefix + b"\x00JSON_SEP\x00" + packed_jsn
    except Exception:
        return None


def _json_decode(data: bytes) -> bytes:
    sep = b"\x00JSON_SEP\x00"
    idx = data.find(sep)
    if idx == -1:
        return data
    prefix = data[:idx]
    packed_jsn = data[idx + len(sep) :]
    packed_obj = json.loads(packed_jsn.decode("utf-8"))
    unpacked_obj = _col_unpack(packed_obj)
    jsn_bytes = json.dumps(unpacked_obj, indent=2).encode("utf-8")
    return prefix + jsn_bytes


def _word_encode(data: bytes) -> bytes:
    if any(b >= 128 for b in data):
        return b"\x00" + data
    words = WORD_RE.findall(data)
    if len(words) < 20:
        return b"\x00" + data
    counts = collections.Counter(w.lower() for w in words)
    vocab = [w for w, c in counts.most_common(126) if len(w) * (c - 1) > 4]
    if not vocab:
        return b"\x00" + data
    w2idx = {w: i + 128 for i, w in enumerate(vocab)}

    def repl(m):
        w = m.group(0)
        lw = w.lower()
        if lw in w2idx:
            tok = bytes([w2idx[lw]])
            if w == lw:
                return tok
            if w[0:1].isupper() and w[1:] == lw[1:]:
                return b"\xff" + tok
        return w

    body = WORD_RE.sub(repl, data)
    # Remove spaces before single-byte tokens (128..253) and capitalize marker \xff
    # Use 0xfe as marker for "space + token" or "space + \xff + token"
    out = bytearray()
    i = 0
    n = len(body)
    while i < n:
        if (
            body[i] == 32
            and i + 1 < n
            and 128 <= body[i + 1] < 254
        ):
            out.append(0xFE)
            out.append(body[i + 1])
            i += 2
        else:
            out.append(body[i])
            i += 1
    header = bytes([len(vocab)]) + b" ".join(vocab) + b"\x00"
    return b"\x01" + header + bytes(out)


def _word_decode(data: bytes) -> bytes:
    mode = data[0]
    if mode == 0:
        return data[1:]
    n_vocab = data[1]
    end_hdr = data.index(b"\x00", 2)
    vocab = data[2:end_hdr].split(b" ") if n_vocab > 0 else []
    body = data[end_hdr + 1 :]

    # First expand 0xfe space-token pairs
    expanded = bytearray()
    i = 0
    n = len(body)
    while i < n:
        b = body[i]
        if b == 0xFE and i + 1 < n:
            expanded.append(32)
            expanded.append(body[i + 1])
            i += 2
        else:
            expanded.append(b)
            i += 1

    # Now expand tokens
    out = bytearray()
    i = 0
    n = len(expanded)
    while i < n:
        b = expanded[i]
        if b == 0xFF and i + 1 < n and 128 <= expanded[i + 1] < 128 + n_vocab:
            w = vocab[expanded[i + 1] - 128]
            out.extend(w[:1].upper() + w[1:])
            i += 2
        elif 128 <= b < 128 + n_vocab:
            out.extend(vocab[b - 128])
            i += 1
        else:
            out.append(b)
            i += 1
    return bytes(out)


def _preprocess(data: bytes) -> bytes:
    j_enc = _try_json_encode(data)
    if j_enc is not None:
        w_enc = _word_encode(j_enc)
        res = b"\x02" + w_enc
    else:
        w_enc = _word_encode(data)
        res = b"\x01" + w_enc
    # Safety check: guarantee 100% lossless round-trip
    if _postprocess(res) == data:
        return res
    return b"\x00" + data


def _postprocess(data: bytes) -> bytes:
    flag = data[0]
    if flag == 0:
        return data[1:]
    if flag == 1:
        return _word_decode(data[1:])
    if flag == 2:
        return _json_decode(_word_decode(data[1:]))
    raise ValueError("Invalid flag")


def compress(data: bytes) -> bytes:
    if not data:
        return b""
    pre = _preprocess(data)
    return lzma.compress(pre, format=lzma.FORMAT_RAW, filters=FILTERS)


def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    pre = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=FILTERS)
    return _postprocess(pre)
