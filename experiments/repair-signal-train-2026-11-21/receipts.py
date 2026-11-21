"""Append-only receipt chain, one JSON object per line, no floats.

A line holds {"seq", "prev", "body", "self"}:
  prev is the SHA-256 of the previous line's bytes (64 zeros for the first),
  self is the SHA-256 of the canonical form of seq, prev and body.
Bodies hold integers and strings only (and lists or dicts of them). Rates are
stored as a numerator and a denominator.

verify recomputes the whole chain and fails on any edit that leaves a later
line, or the line's own self hash, inconsistent. Limit: someone who rewrites
the last line and recomputes its self hash cannot be caught from the file
alone. Keep the head hash somewhere else (verify accepts --head) to close that.

    python3 receipts.py verify FILE [--head HEX]
"""
import hashlib
import json
import os
import sys

ZERO = "0" * 64


class ReceiptError(Exception):
    pass


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def check_plain(obj, where="body"):
    """Integers and strings only. bool, float and None are refused."""
    if isinstance(obj, bool) or obj is None or isinstance(obj, float):
        raise ReceiptError("%s holds a value that is not an integer or a string" % where)
    if isinstance(obj, (int, str)):
        return
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            check_plain(v, "%s[%d]" % (where, i))
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ReceiptError("%s has a key that is not a string" % where)
            check_plain(v, "%s.%s" % (where, k))
        return
    raise ReceiptError("%s holds a value of type %s" % (where, type(obj).__name__))


def _no_float(text):
    raise ReceiptError("a float (%s) appears in the file" % text)


def _read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw and not raw.endswith(b"\n"):
        raise ReceiptError("the file does not end with a newline")
    return [ln for ln in raw.split(b"\n")[:-1]]


def _self_hash(seq, prev, body):
    return hashlib.sha256(_canon({"seq": seq, "prev": prev, "body": body}).encode()).hexdigest()


def verify(path, expect_head=None):
    """Returns (count, head). Raises ReceiptError on the first inconsistency."""
    prev = ZERO
    lines = _read_lines(path)
    for i, ln in enumerate(lines, 1):
        try:
            rec = json.loads(ln.decode("utf-8"), parse_float=_no_float, parse_constant=_no_float)
        except ValueError as exc:
            raise ReceiptError("line %d is not valid JSON: %s" % (i, exc))
        if not isinstance(rec, dict) or set(rec) != {"seq", "prev", "body", "self"}:
            raise ReceiptError("line %d has the wrong fields" % i)
        if rec["seq"] != i:
            raise ReceiptError("line %d has seq %r" % (i, rec["seq"]))
        if rec["prev"] != prev:
            raise ReceiptError("line %d does not chain to line %d" % (i, i - 1))
        check_plain(rec["body"])
        if rec["self"] != _self_hash(rec["seq"], rec["prev"], rec["body"]):
            raise ReceiptError("line %d fails its own hash" % i)
        prev = hashlib.sha256(ln).hexdigest()
    if expect_head is not None and prev != expect_head:
        raise ReceiptError("head %s differs from the expected %s" % (prev, expect_head))
    return len(lines), prev


def append(path, body, expect_head=None):
    """Verifies the existing chain (against expect_head if given), then appends
    one receipt. Returns the new head."""
    check_plain(body)
    count, head = verify(path, expect_head)
    rec = {"seq": count + 1, "prev": head, "body": body}
    rec["self"] = _self_hash(rec["seq"], rec["prev"], rec["body"])
    line = (_canon(rec) + "\n").encode("utf-8")
    with open(path, "ab") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    return hashlib.sha256(line[:-1]).hexdigest()


def bodies(path, expect_head=None):
    verify(path, expect_head)
    return [json.loads(ln.decode("utf-8"))["body"] for ln in _read_lines(path)]


def main(argv):
    if len(argv) < 3 or argv[1] != "verify":
        print("usage: receipts.py verify FILE [--head HEX]")
        return 2
    head = argv[argv.index("--head") + 1] if "--head" in argv else None
    try:
        count, got = verify(argv[2], head)
    except ReceiptError as exc:
        print("FAIL: %s" % exc)
        return 1
    print("OK: %d receipts, head %s" % (count, got))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
