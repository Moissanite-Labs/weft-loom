import sys

_TRANS_TABLES = [bytes(49 if i == c else 48 for i in range(256)) for c in range(128)]

def lcs_length(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return len(a)
    if len(a) > len(b):
        a, b = b, a

    if a.isascii() and b.isascii():
        ba = a.encode('ascii')[::-1]
        bb = b.encode('ascii')
        masks = [0] * 128
        tt = _TRANS_TABLES
        b_trans = ba.translate
        for ch in set(ba) & set(bb):
            masks[ch] = int(b_trans(tt[ch]), 2)
        full = (1 << len(a)) - 1
        S = full
        for byte in bb:
            u = S & masks[byte]
            S = (S + u) | (S - u)
        return len(a) - (S & full).bit_count()

    masks = {ch: 0 for ch in set(a)}
    bit = 1
    for ch in a:
        masks[ch] |= bit
        bit <<= 1
    full = bit - 1
    S = full
    masks_get = masks.get
    for ch in b:
        pm = masks_get(ch, 0)
        u = S & pm
        S = (S + u) | (S - u)
    return len(a) - (S & full).bit_count()

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        a = lines[0] if lines else ""
        b = ""
    else:
        a, b = lines[0], lines[1]
    print(lcs_length(a, b))

if __name__ == "__main__":
    main()
