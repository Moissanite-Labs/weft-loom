import sys


def lcs(a, b):
    # Bit-parallel LCS (Crochemore et al. / Hyyro), using Python big ints.
    if len(a) < len(b):
        a, b = b, a  # masks built over b-shorter? keep bits = len(a) either way fine
    m = len(a)
    if m == 0 or not b:
        return 0
    masks = {}
    bit = 1
    for ch in a:
        masks[ch] = masks.get(ch, 0) | bit
        bit <<= 1
    full = (1 << m) - 1
    v = full
    get = masks.get
    for ch in b:
        mk = get(ch)
        if mk:
            u = v & mk
            v = ((v + u) | (v - u)) & full
    return m - bin(v).count("1")


def main():
    data = sys.stdin.read().split("\n")
    a = data[0].rstrip("\r") if len(data) > 0 else ""
    b = data[1].rstrip("\r") if len(data) > 1 else ""
    sys.stdout.write(str(lcs(a, b)) + "\n")


if __name__ == "__main__":
    main()
