import sys


def lcs(a, b, K=64):
    # Bit-parallel LCS (Crochemore / Hyyro) on Python big ints.
    # Bits span the longer string; the loop runs over the shorter one.
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return 0
    m = len(a)
    common = set(a).intersection(b)
    if not common:
        return 0
    # Build match masks via translate + int(.., 2): bit i set iff a[i] == ch.
    ar = a[::-1]
    table = dict.fromkeys(map(ord, set(a)), "0")
    masks = {}
    for ch in common:
        o = ord(ch)
        table[o] = "1"
        masks[ch] = int(ar.translate(table), 2)
        table[o] = "0"
    if len(common) < len(set(b)):
        b = [c for c in b if c in common]
    seq = list(map(masks.__getitem__, b))
    full = (1 << m) - 1
    v = full
    # High bits (>= m) never influence low bits, so mask only every K steps.
    for i in range(0, len(seq), K):
        for mk in seq[i:i + K]:
            u = v & mk
            v = (v + u) | (v - u)
        v &= full
    return m - v.bit_count()


def main():
    data = sys.stdin.read().split("\n")
    a = data[0].rstrip("\r") if len(data) > 0 else ""
    b = data[1].rstrip("\r") if len(data) > 1 else ""
    sys.stdout.write(str(lcs(a, b)) + "\n")


if __name__ == "__main__":
    main()
