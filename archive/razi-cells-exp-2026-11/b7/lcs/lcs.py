import sys


def _lcs(a, b):
    """Length of the longest common subsequence of two strings.

    Bit-parallel DP: bits of V mark where the current DP row increases.
    Iterating over the shorter string keeps Python-level loop count low,
    while big-integer ops handle the longer string a word at a time.
    """
    if not a or not b:
        return 0
    if a == b:
        return len(a)
    # V has len(b) bits; we iterate once per character of a.  Minimize the
    # number of Python iterations by making a the shorter string.
    if len(a) > len(b):
        a, b = b, a

    masks = {}
    for j, ch in enumerate(b):
        masks[ch] = masks.get(ch, 0) | (1 << j)

    V = 0
    get = masks.get
    for ch in a:
        M = get(ch, 0)
        if not M:
            # A character absent from b cannot change the DP row.
            continue
        x = M | V
        y = (V << 1) | 1
        V = x & ~(x - y)
    return V.bit_count()


def main():
    data = sys.stdin.read()
    lines = data.split('\n')
    a = lines[0] if lines else ''
    b = lines[1] if len(lines) > 1 else ''
    # Defensive: handle CRLF if universal-newline translation did not.
    if a.endswith('\r'):
        a = a[:-1]
    if b.endswith('\r'):
        b = b[:-1]
    sys.stdout.write(str(_lcs(a, b)) + '\n')


if __name__ == '__main__':
    main()
