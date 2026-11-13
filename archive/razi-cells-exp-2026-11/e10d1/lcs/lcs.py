import sys

def lcs_len(a, b):
    # Bit-parallel LCS (Hyyro / Allison-Dix): O(len(a)) big-int ops of len(b) bits.
    if len(a) < len(b):
        a, b = b, a
    m = len(b)
    if m == 0:
        return 0
    masks = {}
    for i, ch in enumerate(b):
        masks[ch] = masks.get(ch, 0) | (1 << i)
    full = (1 << m) - 1
    v = full
    get = masks.get
    for ch in a:
        u = v & get(ch, 0)
        v = ((v + u) | (v - u)) & full
    return m - bin(v).count("1")

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    a = a.rstrip("\r")
    b = b.rstrip("\r")
    print(lcs_len(a, b))

if __name__ == "__main__":
    main()
