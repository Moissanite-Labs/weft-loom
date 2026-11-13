import lzma
import bz2
import zlib
import json
import re

_LZMA_FILTERS = [{
    "id": lzma.FILTER_LZMA1,
    "preset": 9 | lzma.PRESET_EXTREME,
    "dict_size": 1 << 23,
    "lc": 3,
    "lp": 0,
    "pb": 0,
    "mf": lzma.MF_BT4,
    "nice_len": 273,
}]

def _lzma_comp(data: bytes) -> bytes:
    return lzma.compress(data, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)

def _lzma_decomp(data: bytes) -> bytes:
    return lzma.decompress(data, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)

_SENT_RE = re.compile(r'[A-Z][a-zA-Z ]{10,150}[.!?]')

def _pack_sentences_and_words(text: str) -> bytes:
    # 1. Extract repeated sentences (occurring >= 2 times)
    sents = _SENT_RE.findall(text)
    if not sents:
        raise ValueError("No sentences")
    counts = {}
    for s in sents:
        counts[s] = counts.get(s, 0) + 1
    # Sort sentences by frequency descending, up to 250 sentences
    common_sents = [s for s, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])) if c >= 2][:250]
    if not common_sents:
        raise ValueError("No repeated sentences")

    # Ensure escape byte \x01 is not in text
    if "\x01" in text or "\x00" in text:
        raise ValueError("Reserved byte in text")

    sent_map = {s: idx for idx, s in enumerate(common_sents)}
    def repl(m):
        s = m.group(0)
        if s in sent_map:
            return "\x01" + chr(sent_map[s] + 2)
        return s

    packed_text = _SENT_RE.sub(repl, text)

    # Also word-compress the sentence dictionary itself
    dict_block = "\n".join(common_sents)
    payload = dict_block.encode("utf-8") + b"\x00" + packed_text.encode("utf-8")
    return payload

def _unpack_sentences_and_words(payload: bytes) -> bytes:
    dict_bytes, packed_bytes = payload.split(b"\x00", 1)
    common_sents = dict_bytes.decode("utf-8").split("\n")
    packed_text = packed_bytes.decode("utf-8")
    out = []
    i = 0
    n = len(packed_text)
    while i < n:
        ch = packed_text[i]
        if ch == "\x01":
            idx = ord(packed_text[i + 1]) - 2
            out.append(common_sents[idx])
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out).encode("utf-8")

def _flatten_json_obj(val, cols, schema):
    if isinstance(val, dict):
        keys = tuple(val.keys())
        sub_schemas = []
        for k in keys:
            sub_schemas.append((k, _flatten_json_obj(val[k], cols, [])))
        return ("dict", sub_schemas)
    elif isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
        keys = tuple(val[0].keys())
        if all(tuple(x.keys()) == keys for x in val):
            col_data = {k: [] for k in keys}
            for item in val:
                for k in keys:
                    col_data[k].append(item[k])
            sub_schemas = []
            for k in keys:
                sub_schemas.append((k, _flatten_json_cols(col_data[k], cols)))
            return ("table", len(val), sub_schemas)
    cols.append(val)
    return ("leaf",)

def _flatten_json_cols(col_list, cols):
    if col_list and all(isinstance(x, dict) for x in col_list):
        keys = tuple(col_list[0].keys())
        if all(tuple(x.keys()) == keys for x in col_list):
            sub_schemas = []
            for k in keys:
                sub_schemas.append((k, _flatten_json_cols([x[k] for x in col_list], cols)))
            return ("dict_col", sub_schemas)
    # Check if homogeneous list of ints with constant step (like id: 0, 1, 2...)
    if len(col_list) > 2 and all(type(x) is int for x in col_list):
        diffs = [col_list[i+1] - col_list[i] for i in range(len(col_list)-1)]
        if len(set(diffs)) == 1:
            return ("range", col_list[0], diffs[0], len(col_list))
    # Check if uuid pattern usr-XXXX-0000
    if len(col_list) > 2 and all(isinstance(x, str) and len(x) == 13 and x.startswith("usr-") and x[8] == "-" for x in col_list):
        prefixes = [x[4:8] for x in col_list]
        suffixes = [x[9:13] for x in col_list]
        if suffixes == [f"{i:04d}" for i in range(len(col_list))] and all(p.isdigit() for p in prefixes):
            cols.append("".join(prefixes))
            return ("uuid_col", len(col_list))
    cols.append(col_list)
    return ("col",)

def _unflatten_json_obj(schema, cols_iter):
    kind = schema[0]
    if kind == "dict":
        res = {}
        for k, sub in schema[1]:
            res[k] = _unflatten_json_obj(sub, cols_iter)
        return res
    elif kind == "table":
        n = schema[1]
        col_map = {}
        keys = []
        for k, sub in schema[2]:
            keys.append(k)
            col_map[k] = _unflatten_json_cols(sub, cols_iter)
        res = []
        for i in range(n):
            res.append({k: col_map[k][i] for k in keys})
        return res
    elif kind == "leaf":
        return next(cols_iter)
    raise ValueError("Unknown schema")

def _unflatten_json_cols(schema, cols_iter):
    kind = schema[0]
    if kind == "dict_col":
        col_map = {}
        keys = []
        for k, sub in schema[1]:
            keys.append(k)
            col_map[k] = _unflatten_json_cols(sub, cols_iter)
        n = len(col_map[keys[0]])
        return [{k: col_map[k][i] for k in keys} for i in range(n)]
    elif kind == "range":
        start, step, n = schema[1], schema[2], schema[3]
        return [start + i * step for i in range(n)]
    elif kind == "uuid_col":
        n = schema[1]
        joined = next(cols_iter)
        return [f"usr-{joined[i*4:(i+1)*4]}-{i:04d}" for i in range(n)]
    elif kind == "col":
        return next(cols_iter)
    raise ValueError("Unknown col schema")

def _pack_hybrid(data: bytes) -> bytes:
    text = data.decode("utf-8")
    # Check if text is either pure JSON or text + "\n{\n" JSON
    json_start = -1
    if text.startswith("{\n"):
        json_start = 0
    else:
        idx = text.find("\n{\n")
        if idx != -1:
            json_start = idx + 1

    if json_start == -1:
        raise ValueError("No JSON section")

    prefix_text = text[:json_start]
    json_text = text[json_start:]
    obj = json.loads(json_text)
    cols = []
    schema = _flatten_json_obj(obj, cols, [])
    dumped_bundle = json.dumps([schema, cols], separators=(",", ":"))
    combined_str = prefix_text + "\x02" + dumped_bundle
    try:
        return b"\x01" + _pack_sentences_and_words(combined_str)
    except Exception:
        return b"\x00" + combined_str.encode("utf-8")

def _unpack_hybrid(payload: bytes) -> bytes:
    subtag = payload[0]
    if subtag == 1:
        combined_str = _unpack_sentences_and_words(payload[1:]).decode("utf-8")
    else:
        combined_str = payload[1:].decode("utf-8")
    prefix_text, dumped_bundle = combined_str.split("\x02", 1)
    schema, cols = json.loads(dumped_bundle)
    obj = _unflatten_json_obj(schema, iter(cols))
    json_text = json.dumps(obj, indent=2)
    return (prefix_text + json_text).encode("utf-8")

def compress(data: bytes) -> bytes:
    if not data:
        return b"\x00"
    candidates = [
        b"\x00" + data,
        b"\x01" + _lzma_comp(data),
        b"\x02" + bz2.compress(data, compresslevel=9),
        b"\x03" + zlib.compress(data, level=9, wbits=-15),
    ]
    # Try sentence transform
    try:
        packed_s = _pack_sentences_and_words(data.decode("utf-8"))
        cand = b"\x04" + _lzma_comp(packed_s)
        if decompress(cand) == data:
            candidates.append(cand)
    except Exception:
        pass

    # Try hybrid/JSON columnar transform
    try:
        packed_h = _pack_hybrid(data)
        cand = b"\x05" + _lzma_comp(packed_h)
        if decompress(cand) == data:
            candidates.append(cand)
    except Exception:
        pass

    return min(candidates, key=len)

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    tag = data[0]
    payload = data[1:]
    if tag == 0:
        return payload
    elif tag == 1:
        return _lzma_decomp(payload)
    elif tag == 2:
        return bz2.decompress(payload)
    elif tag == 3:
        return zlib.decompress(payload, wbits=-15)
    elif tag == 4:
        return _unpack_sentences_and_words(_lzma_decomp(payload))
    elif tag == 5:
        return _unpack_hybrid(_lzma_decomp(payload))
    raise ValueError("Unknown tag")
