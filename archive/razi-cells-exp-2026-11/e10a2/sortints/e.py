import sys
def slow(data):
    a = sorted(map(int, data.split()))
    if a:
        sys.stdout.write('\n'.join(map(str, a)))
        sys.stdout.write('\n')
def swar(x):
    x = (x * 2561) >> 8
    x = ((x & 0x00ff00ff00ff00ff) * 6553601) >> 16
    x = ((x & 0x0000ffff0000ffff) * 42949672960001) >> 32
    return x
TBL = bytes(0 if (9 <= c <= 13 or c == 32) else 1 if (48 <= c <= 57 or c == 45) else 2 for c in range(256))
def fast(np, data):
    data = b'\n' * 16 + data + b'\n' * 16
    L = len(data)
    t = data.translate(TBL)
    if b'\x02' in t:
        return False
    buf = np.frombuffer(data, np.uint8)
    tok = np.frombuffer(t, np.bool_)
    b = np.flatnonzero(tok[1:] != tok[:-1])
    if b.size == 0:
        return False
    b += 1
    starts = b[0::2]
    ends = b[1::2]
    N = starts.size
    neg = buf[starts] == 45
    if data.count(b'-') != np.count_nonzero(neg):
        return False
    ln = ends - starts
    nd = ln - neg
    fd = buf[starts + neg]
    if int(nd.min()) < 1:
        return False
    if ((fd == 48) & ((nd > 1) | neg)).any():
        return False
    maxd = int(nd.max())
    if maxd > 16:
        return False
    view = np.ndarray(shape=(L - 7,), dtype='<u8', buffer=data, strides=(1,))
    F = 0xFFFFFFFFFFFFFFFF
    masks = np.array([0] + [((F << (8 * (8 - n))) & F) & 0x0f0f0f0f0f0f0f0f for n in range(1, 9)], dtype=np.uint64)
    val = swar(view[ends - 8] & masks[np.minimum(nd, 8)])
    if maxd > 8:
        hi = swar(view[ends - 16] & masks[np.clip(nd - 8, 0, 8)])
        val += hi * np.uint64(100000000)
    val = val.astype(np.int64)
    val = np.where(neg, -val, val)
    shift = max(1, (N - 1).bit_length())
    if 10 ** maxd < (1 << (62 - shift)):
        key = (val << shift) | np.arange(N, dtype=np.int64)
        key.sort()
        order = key & ((1 << shift) - 1)
    else:
        order = np.argsort(val, kind='stable')
    ss = starts[order]
    ls = ln[order]
    ls += 1
    cs = np.cumsum(ls)
    total = int(cs[-1])
    if int(ln.max()) < 16:
        out = bytearray(total + 16)
        ov = np.ndarray(shape=(total + 9,), dtype='<u8', buffer=out, strides=(1,))
        pa = cs - ls
        pa += 8
        ov[pa] = view[ss]
        ss += ls
        ss -= 8
        w = view[ss]
        ov[cs[::-1]] = w[::-1]
        cs += 7
        np.frombuffer(out, np.uint8)[cs] = 10
        sys.stdout.buffer.write(memoryview(out)[8:8 + total])
        return True
    ss -= cs
    ss += ls
    src = np.repeat(ss, ls)
    src += np.arange(total, dtype=src.dtype)
    out = buf[src]
    cs -= 1
    out[cs] = 10
    sys.stdout.buffer.write(out.data)
    return True
def main():
    data = sys.stdin.buffer.read()
    if len(data) < 4096:
        return slow(data)
    try:
        import numpy as np
        ok = fast(np, data)
    except Exception:
        ok = False
    if not ok:
        slow(data)
main()
