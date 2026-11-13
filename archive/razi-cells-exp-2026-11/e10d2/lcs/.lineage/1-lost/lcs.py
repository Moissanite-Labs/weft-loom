import sys

def lcs_len(a, b):
    # Bit-parallel LCS (Hyyro) using Python big ints.
    if len(a) > len(b):
        a, b = b, a
    n = len(b)
    if n == 0:
        return 0
    pm = {}
    for i, ch in enumerate(b):
        pm[ch] = pm.get(ch, 0) | (1 << i)
    mask = (1 << n) - 1
    get = pm.get
    ms = [m for m in map(get, a) if m is not None]
    S = mask
    for m in ms:
        u = S & m
        S = (S + u) | (S ^ u)
    S &= mask
    try:
        return n - S.bit_count()
    except AttributeError:
        return n - bin(S).count("1")

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    print(lcs_len(a.rstrip("\r"), b.rstrip("\r")))

if __name__ == "__main__":
    main()
