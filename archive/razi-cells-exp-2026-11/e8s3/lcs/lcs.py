import os
import sys

def lcs_length(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return len(a)
    cp = len(os.path.commonprefix((a, b)))
    if cp:
        a = a[cp:]
        b = b[cp:]
        if not a or not b:
            return cp
    cs = len(os.path.commonprefix((a[::-1], b[::-1])))
    if cs:
        a = a[:-cs]
        b = b[:-cs]
        if not a or not b:
            return cp + cs
    if len(a) < len(b):
        a, b = b, a
    pos = {}
    get = pos.get
    for i, ch in enumerate(b):
        pos[ch] = get(ch, 0) | (1 << i)
    
    M = (1 << len(b)) - 1
    S = M
    for P in map(get, a):
        if P:
            u = S & P
            S = (S + u) | (S - u)
    return cp + cs + len(b) - (S & M).bit_count()

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
