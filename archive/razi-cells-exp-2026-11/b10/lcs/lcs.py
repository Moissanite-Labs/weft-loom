import sys

def lcs(a: str, b: str) -> int:
    if a == b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    nb = len(b)
    if not nb:
        return 0
    common = set(a) & set(b)
    if not common:
        return 0
    pos = {}
    if len(common) <= 32:
        rb = b[::-1]
        z = {ord(c): 48 for c in set(b)}
        for ch in common:
            o = ord(ch)
            z[o] = 49
            pos[ch] = int(rb.translate(z), 2)
            z[o] = 48
    else:
        b_find = b.find
        for ch in common:
            mask = 0
            i = b_find(ch)
            while i != -1:
                mask |= 1 << i
                i = b_find(ch, i + 1)
            pos[ch] = mask
    pos_get = pos.get
    S = (1 << nb) - 1
    for ch in a:
        if p := pos_get(ch):
            u = S & p
            S = (S + u) | (S - u)
    return nb - (S & ((1 << nb) - 1)).bit_count()

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        a = lines[0] if lines else ""
        b = ""
    else:
        a, b = lines[0], lines[1]
    print(lcs(a, b))

if __name__ == "__main__":
    main()
