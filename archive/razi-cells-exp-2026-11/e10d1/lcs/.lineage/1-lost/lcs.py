import sys

def lcs_len(a, b):
    # Bit-parallel LCS (Hyyro / Allison-Dix): O(len(a)) big-int ops of len(b) bits.
    if len(a) < len(b):
        a, b = b, a
    m = len(b)
    if m == 0:
        return 0
    full = (1 << m) - 1
    v = full
    try:
        ab = a.encode("latin-1")
        bb = b.encode("latin-1")
    except UnicodeEncodeError:
        ab = bb = None
    if ab is not None:
        masks = [0] * 256
        bit = 1
        for c in bb:
            masks[c] |= bit
            bit <<= 1
        seq = ab
    else:
        md = {}
        bit = 1
        for ch in b:
            md[ch] = md.get(ch, 0) | bit
            bit <<= 1
        masks = md
        seq = a
        get = md.get
    n = len(seq)
    K = 64
    # Garbage bits above m grow by at most one bit per iteration and never
    # influence bits below m (carries go upward, u is a subset of v so no
    # borrows), so masking every K iterations is safe.
    if ab is not None:
        for i in range(0, n, K):
            for c in seq[i:i + K]:
                u = v & masks[c]
                v = (v + u) | (v - u)
            v &= full
    else:
        for i in range(0, n, K):
            for ch in seq[i:i + K]:
                u = v & get(ch, 0)
                v = (v + u) | (v - u)
            v &= full
    v &= full
    try:
        cnt = v.bit_count()
    except AttributeError:
        cnt = bin(v).count("1")
    return m - cnt

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    a = a.rstrip("\r")
    b = b.rstrip("\r")
    print(lcs_len(a, b))

if __name__ == "__main__":
    main()
