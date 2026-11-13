import sys

_Z = b'0' * 256

def _masks(a):
    try:
        ab = a.encode('latin-1')[::-1]
    except UnicodeEncodeError:
        masks = {}
        bit = 1
        for ch in a:
            masks[ch] = masks.get(ch, 0) | bit
            bit <<= 1
        return masks
    return {chr(c): int(ab.translate(_Z[:c] + b'1' + _Z[c + 1:]), 2) for c in set(ab)}

def lcs(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return 0
    m = len(a)
    masks = _masks(a)
    if not masks.keys() >= set(b):
        b = ''.join([ch for ch in b if ch in masks])
    full = (1 << m) - 1
    v = full
    ms = list(map(masks.__getitem__, b))
    for i in range(0, len(ms), 250):
        for mk in ms[i:i + 250]:
            u = v & mk
            v = (v + u) | (v ^ u)
        v &= full
    return m - v.bit_count()

def main():
    data = sys.stdin.read().split("\n")
    a = data[0].rstrip("\r") if len(data) > 0 else ""
    b = data[1].rstrip("\r") if len(data) > 1 else ""
    print(lcs(a, b))

if __name__ == "__main__":
    main()
