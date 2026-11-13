import sys


def lcs_length(a, b):
    """Bit-parallel LCS length (Hyyrö / Crochemore et al.).

    a and b are bytes-like objects (iterating yields ints).
    Builds position bitmasks for the longer string and scans the shorter one.
    """
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    m = len(a)
    masks = {}
    get = masks.get
    for i, ch in enumerate(a):
        masks[ch] = get(ch, 0) | (1 << i)
    full = (1 << m) - 1
    V = full
    for ch in b:
        p = masks.get(ch)
        if p is None:
            continue
        U = V & p
        V = ((V + U) | (V - U)) & full
    return m - bin(V).count('1')


def main():
    data = sys.stdin.buffer.read().split(b'\n')
    a = data[0].rstrip(b'\r') if len(data) > 0 else b''
    b = data[1].rstrip(b'\r') if len(data) > 1 else b''
    sys.stdout.write(str(lcs_length(a, b)))


if __name__ == '__main__':
    main()
