import sys

def slow(toks, w):
    a = list(map(int, toks))
    a.sort()
    w.write(('\n'.join(map(str, a)) + '\n').encode())

def noncanon(data, toks):
    if b'+' in data or b'_' in data or b'-0' in data:
        return True
    z = (data[:1] == b'0') + sum(data.count(c) for c in (b' 0', b'\n0', b'\t0', b'\r0', b'\x0b0', b'\x0c0'))
    return z != toks.count(b'0')

def main():
    data = sys.stdin.buffer.read()
    toks = data.split()
    if not toks:
        return
    w = sys.stdout.buffer
    if noncanon(data, toks):
        return slow(toks, w)
    import numpy as np
    n = len(toks)
    try:
        k = np.fromiter(map(int, toks), dtype=np.int64, count=n)
    except OverflowError:
        toks.sort(key=int)
        w.write(b'\n'.join(toks))
        w.write(b'\n')
        return
    order = np.argsort(k)
    out = np.array(toks, dtype=object)[order].tolist()
    w.write(b'\n'.join(out))
    w.write(b'\n')

main()
