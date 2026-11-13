import sys

_ALL = frozenset(range(256))

def _generic(a, b):
    m = len(a)
    masks = {}
    bit = 1
    for ch in a:
        masks[ch] = masks.get(ch, 0) | bit
        bit <<= 1
    full = (1 << m) - 1
    v = full
    get = masks.get
    for ch in b:
        mk = get(ch)
        if mk:
            u = v & mk
            v = ((v + u) | (v ^ u)) & full
    return m - v.bit_count()

def _core(a, b):
    m = len(a)
    sa = set(a)
    b = b.translate(None, bytes(_ALL - sa))
    if not b:
        return 0
    ra = a[::-1]
    full = (1 << m) - 1
    tbl = [None] * 256
    zeros = b"0" * 256
    for c in sa:
        t = bytearray(zeros)
        t[c] = 49
        mk = int(ra.translate(t), 2)
        tbl[c] = (mk, full ^ mk)
    v = full
    for mk, nmk in map(tbl.__getitem__, b):
        v = (v + (v & mk)) | (v & nmk)
    return m - (v & full).bit_count()

def lcs(a, b):
    if not a or not b:
        return 0
    if len(a) > len(b):
        a, b = b, a
    if isinstance(a, (bytes, bytearray)) and isinstance(b, (bytes, bytearray)):
        return _core(bytes(a), bytes(b))
    if isinstance(a, str) and isinstance(b, str):
        sa = set(a)
        if len(sa) <= 256:
            mp = {ch: i for i, ch in enumerate(sa)}
            return _core(bytes(map(mp.__getitem__, a)), bytes([mp[ch] for ch in b if ch in mp]))
    return _generic(a, b)

def main():
    data = sys.stdin.buffer.read()
    if data.isascii():
        lines = data.split(b"\n")
        a = lines[0].rstrip(b"\r")
        b = lines[1].rstrip(b"\r") if len(lines) > 1 else b""
    else:
        lines = data.decode("utf-8", "surrogateescape").split("\n")
        a = lines[0].rstrip("\r")
        b = lines[1].rstrip("\r") if len(lines) > 1 else ""
    sys.stdout.write(str(lcs(a, b)) + "\n")

if __name__ == "__main__":
    main()
