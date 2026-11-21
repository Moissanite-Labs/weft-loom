"""Advocate pass: read the DATA object from a saved qwen-neuron-map page (read only).

Written fresh for the advocate pass; shares no code with the sibling's bridge.py or the
evaluator's scripts. Stdlib only. The page is untrusted data: it is parsed as JSON, never run.
"""
import base64
import json


class PageError(Exception):
    pass


def load_data(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    key = "DATA = "
    at = text.find(key)
    if at < 0:
        raise PageError("no DATA object in " + path)
    brace = text.find("{", at)
    obj, _end = json.JSONDecoder().raw_decode(text, brace)
    return obj


def group_ids(data):
    """Per-neuron group id (Uint16 little endian), 65535 = no group."""
    raw = base64.b64decode(data["structures"]["ids"])
    n = int(data["n"])
    if len(raw) != 2 * n:
        raise PageError("ids length %d != 2n %d" % (len(raw), 2 * n))
    return [raw[2 * i] | (raw[2 * i + 1] << 8) for i in range(n)]


def family_of_neuron(data, ids):
    fam = data["structures"]["familyOf"]
    return [(-1 if g == 65535 else fam[g]) for g in ids]


def kind_of_neuron(data, ids):
    reg = data["structures"]["regionOf"]
    return [(-1 if g == 65535 else reg[g]) for g in ids]
