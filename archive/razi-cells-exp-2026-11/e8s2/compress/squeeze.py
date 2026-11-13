import json
import lzma
import re

_FILTERS = [{
    "id": lzma.FILTER_LZMA1,
    "preset": 9 | lzma.PRESET_EXTREME,
    "lc": 3,
    "lp": 0,
    "pb": 0,
    "nice_len": 273,
    "depth": 1000,
}]

_CAP_RE = re.compile(rb'(?<![A-Za-z0-9_])([A-Z])([a-z]{1,30})(?![A-Za-z0-9_])')
_UNCAP_RE = re.compile(rb'\x01([a-z])')

def _cap_sub(m):
    return b'\x01' + bytes([m.group(1)[0] + 32]) + m.group(2)

def _uncap_sub(m):
    return bytes([m.group(1)[0] - 32])

def _pack_records(records):
    # Columnar transform of list of uniform dicts (with optional nested dict 'metadata')
    if not isinstance(records, list) or not records or not all(isinstance(r, dict) for r in records):
        return None
    keys = list(records[0].keys())
    if not all(list(r.keys()) == keys for r in records):
        return None
    cols = {}
    for k in keys:
        vals = [r[k] for r in records]
        if all(isinstance(v, dict) for v in vals) and vals:
            subkeys = list(vals[0].keys())
            if all(list(v.keys()) == subkeys for v in vals):
                cols[k] = {"__sub__": subkeys, "cols": {sk: [v[sk] for v in vals] for sk in subkeys}}
                continue
        cols[k] = vals
    return {"__keys__": keys, "__n__": len(records), "__cols__": cols}

def _unpack_records(packed):
    keys = packed["__keys__"]
    n = packed["__n__"]
    cols = packed["__cols__"]
    rebuilt_cols = {}
    for k in keys:
        c = cols[k]
        if isinstance(c, dict) and "__sub__" in c:
            subkeys = c["__sub__"]
            subcols = c["cols"]
            rebuilt_cols[k] = [{sk: subcols[sk][i] for sk in subkeys} for i in range(n)]
        else:
            rebuilt_cols[k] = c
    return [{k: rebuilt_cols[k][i] for k in keys} for i in range(n)]

def _try_transform_json_block(text: str):
    obj = json.loads(text)
    if isinstance(obj, dict) and "items" in obj and isinstance(obj["items"], list):
        packed = _pack_records(obj["items"])
        if packed is not None:
            new_obj = dict(obj)
            new_obj["items"] = packed
            return json.dumps(new_obj, separators=(",", ":"))
    return None

def _restore_json_block(s: str) -> str:
    obj = json.loads(s)
    if isinstance(obj, dict) and "items" in obj and isinstance(obj["items"], dict) and "__keys__" in obj["items"]:
        obj["items"] = _unpack_records(obj["items"])
    return json.dumps(obj, indent=2)

def _forward(data: bytes) -> bytes:
    if b'\x00' in data or b'\x01' in data or b'\x02' in data:
        return b'\x00' + data
    try:
        s = data.decode('utf-8')
        # Case 1: pure indented JSON or text + "\n{\n" indented JSON
        idx = s.find('\n{\n  "version":')
        if s.startswith('{\n  "version":') or idx != -1:
            if idx == -1:
                prefix = ""
                jpart = s
                mode = 2
            else:
                prefix = s[:idx]
                jpart = s[idx + 1:]
                mode = 3
            packed_j = _try_transform_json_block(jpart)
            if packed_j is not None:
                if mode == 2:
                    cand = b'\x02' + _CAP_RE.sub(_cap_sub, packed_j.encode('utf-8'))
                else:
                    p_bytes = _CAP_RE.sub(_cap_sub, prefix.encode('utf-8'))
                    j_bytes = _CAP_RE.sub(_cap_sub, packed_j.encode('utf-8'))
                    cand = b'\x03' + p_bytes + b'\x00' + j_bytes
                if _inverse(cand) == data:
                    return cand
        # Case 2: mixed text + JSON lines
        lines = s.split('\n')
        json_idxs = []
        json_objs = []
        for i, line in enumerate(lines):
            if line.startswith('{"id": ') and line.endswith('}'):
                json_idxs.append(i)
                json_objs.append(json.loads(line))
        if len(json_objs) >= 10:
            packed = _pack_records(json_objs)
            if packed is not None:
                text_lines = [line for i, line in enumerate(lines) if not (line.startswith('{"id": ') and line.endswith('}'))]
                meta = json.dumps({"idxs": json_idxs, "packed": packed}, separators=(",", ":"))
                t_part = "\n".join(text_lines)
                cand_body = _CAP_RE.sub(_cap_sub, (t_part + "\x00" + meta).encode('utf-8'))
                cand = b'\x04' + cand_body
                if _inverse(cand) == data:
                    return cand
    except Exception:
        pass
    t = _CAP_RE.sub(_cap_sub, data)
    cand = b'\x01' + t
    if _inverse(cand) == data:
        return cand
    return b'\x00' + data

def _inverse(b: bytes) -> bytes:
    tag = b[0]
    payload = b[1:]
    if tag == 0:
        return payload
    if tag == 1:
        return _UNCAP_RE.sub(_uncap_sub, payload)
    if tag == 2:
        s = _UNCAP_RE.sub(_uncap_sub, payload).decode('utf-8')
        return _restore_json_block(s).encode('utf-8')
    if tag == 3:
        p_bytes, j_bytes = payload.split(b'\x00', 1)
        prefix = _UNCAP_RE.sub(_uncap_sub, p_bytes).decode('utf-8')
        j_str = _UNCAP_RE.sub(_uncap_sub, j_bytes).decode('utf-8')
        return (prefix + '\n' + _restore_json_block(j_str)).encode('utf-8')
    if tag == 4:
        restored = _UNCAP_RE.sub(_uncap_sub, payload).decode('utf-8')
        t_part, meta_s = restored.split('\x00', 1)
        meta = json.loads(meta_s)
        idxs = set(meta["idxs"])
        objs = _unpack_records(meta["packed"])
        text_lines = t_part.split('\n') if t_part else []
        total = len(idxs) + len(text_lines)
        out = []
        ti = 0
        ji = 0
        for i in range(total):
            if i in idxs:
                out.append(json.dumps(objs[ji]))
                ji += 1
            else:
                out.append(text_lines[ti])
                ti += 1
        return "\n".join(out).encode('utf-8')
    return payload

def compress(data: bytes) -> bytes:
    transformed = _forward(data)
    return lzma.compress(transformed, format=lzma.FORMAT_RAW, filters=_FILTERS)

def decompress(data: bytes) -> bytes:
    raw = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=_FILTERS)
    return _inverse(raw)
