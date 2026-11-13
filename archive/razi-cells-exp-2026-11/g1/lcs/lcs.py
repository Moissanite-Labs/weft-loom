import sys


def lcs_len(a, b):
    """Length of longest common subsequence via Hyyro's bit-parallel algorithm."""
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a  # keep masks on the shorter string
    m = len(b)
    mask = {}
    for i, ch in enumerate(b):
        mask[ch] = mask.get(ch, 0) | (1 << i)
    low = (1 << m) - 1
    V = low
    get = mask.get
    for ch in a:
        U = V & get(ch, 0)
        V = (V + U) | (V - U)
    return m - bin(V & low).count('1')


def main():
    lines = sys.stdin.read().splitlines()
    a = lines[0] if len(lines) > 0 else ''
    b = lines[1] if len(lines) > 1 else ''
    sys.stdout.write(str(lcs_len(a, b)) + '\n')


if __name__ == '__main__':
    main()
