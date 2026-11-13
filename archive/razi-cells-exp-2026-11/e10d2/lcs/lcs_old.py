import sys

def lcs_len(a, b):
    # Bit-parallel LCS (Hyyro / Allison-Dix) using Python big ints.
    if len(a) < len(b):
        a, b = b, a
    n = len(b)
    if n == 0:
        return 0
    pm = {}
    for i, ch in enumerate(b):
        pm[ch] = pm.get(ch, 0) | (1 << i)
    mask = (1 << n) - 1
    S = mask  # all ones
    for ch in a:
        m = pm.get(ch)
        if m is None:
            continue
        u = S & m
        S = ((S + u) | (S - u)) & mask
    # number of zero bits in S among n bits
    return n - bin(S).count("1")

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    a = a.rstrip("\r")
    b = b.rstrip("\r")
    print(lcs_len(a, b))

if __name__ == "__main__":
    main()
