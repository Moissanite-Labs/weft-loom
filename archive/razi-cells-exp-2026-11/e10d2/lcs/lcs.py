import sys

def lcs_len(a, b):
    # Bit-parallel LCS (Hyyro) using Python big ints.
    # loop over the shorter string; bit-vector spans the longer (fewer Python iterations)
    if len(a) > len(b):
        a, b = b, a
    n = len(b)
    if n == 0:
        return 0
    pm = {}
    for i, ch in enumerate(b):
        pm[ch] = pm.get(ch, 0) | (1 << i)
    mask = (1 << n) - 1
    # precompute complement masks; high garbage bits never affect low n bits
    nm = {ch: mask ^ m for ch, m in pm.items()}
    S = mask
    get = pm.get
    for ch in a:
        m = get(ch)
        if m is None:
            continue
        S = (S + (S & m)) | (S & nm[ch])
    S &= mask
    return n - bin(S).count("1")

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    print(lcs_len(a.rstrip("\r"), b.rstrip("\r")))

if __name__ == "__main__":
    main()
