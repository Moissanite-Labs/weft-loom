import sys

def lcs_len(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return 0
    n = len(a)
    masks = {}
    bit = 1
    for ch in a:
        masks[ch] = masks.get(ch, 0) | bit
        bit <<= 1
    ones = bit - 1
    nm = {}
    for ch, m in masks.items():
        nm[ch] = (m, ones ^ m)
    V = ones
    get = nm.get
    for ch in b:
        t = get(ch)
        if t is None:
            continue
        M, NM = t
        V = (V + (V & M)) | (V & NM)
    return n - (V & ones).bit_count()

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    a = a.rstrip("\r")
    b = b.rstrip("\r")
    print(lcs_len(a, b))

if __name__ == "__main__":
    main()
