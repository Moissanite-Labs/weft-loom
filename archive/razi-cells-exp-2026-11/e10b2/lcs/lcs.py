import sys


def lcs(a, b):
    if len(a) < len(b):
        a, b = b, a
    # bit-parallel (Crochemore/Hyyro): bits over b, iterate over a
    m = len(b)
    if m == 0:
        return 0
    masks = {}
    bit = 1
    for ch in b:
        masks[ch] = masks.get(ch, 0) | bit
        bit <<= 1
    full = (1 << m) - 1
    v = full
    get = masks.get
    ml = [get(c, 0) for c in a]
    # Carries only travel upward, so bits above m never affect the low m
    # bits; trim them once per chunk instead of on every character.
    for i in range(0, len(ml), 32):
        for mk in ml[i:i + 32]:
            u = v & mk
            v = (v + u) | (v - u)
        v &= full
    return m - bin(v).count("1")


def main():
    data = sys.stdin.read().split("\n")
    a = data[0].rstrip("\r") if len(data) > 0 else ""
    b = data[1].rstrip("\r") if len(data) > 1 else ""
    print(lcs(a, b))


if __name__ == "__main__":
    main()
