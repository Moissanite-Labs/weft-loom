import sys

def lcs_len(s1: str, s2: str) -> int:
    n1, n2 = len(s1), len(s2)
    if not n1 or not n2:
        return 0
    if s1 == s2:
        return n1
    if n1 > n2:
        s1, s2 = s2, s1
        n1, n2 = n2, n1
    if s1.isascii() and s2.isascii():
        pm = [0] * 128
        b1 = s1.encode()
        b2 = s2.encode()
        for i, b in enumerate(b1):
            pm[b] |= 1 << i
        mask = (1 << n1) - 1
        S = mask
        for b in b2:
            P = pm[b]
            if P:
                u = S & P
                S = (S + u) | (S ^ u)
        return n1 - (S & mask).bit_count()
    pm = {}
    for i, ch in enumerate(s1):
        pm[ch] = pm.get(ch, 0) | (1 << i)
    mask = (1 << n1) - 1
    S = mask
    get = pm.get
    for ch in s2:
        P = get(ch)
        if P is not None:
            u = S & P
            S = (S + u) | (S ^ u)
    return n1 - (S & mask).bit_count()

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        s1 = lines[0] if lines else ""
        s2 = ""
    else:
        s1, s2 = lines[0], lines[1]
    print(lcs_len(s1, s2))

if __name__ == "__main__":
    main()
