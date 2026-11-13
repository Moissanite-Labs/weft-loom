import sys


def lcs_length(s1: str, s2: str) -> int:
    if not s1 or not s2:
        return 0
    if s1 == s2:
        return len(s1)

    if len(s1) > len(s2):
        s1, s2 = s2, s1

    masks = {}
    for i, ch in enumerate(s2):
        masks[ch] = masks.get(ch, 0) | (1 << i)

    P = 0
    get_mask = masks.get
    for ch in s1:
        m = get_mask(ch, 0)
        if m:
            X = P | m
            P = X & (X ^ (X - ((P << 1) | 1)))

    return P.bit_count()


def main():
    lines = sys.stdin.buffer.read().splitlines()
    s1 = lines[0].decode('utf-8', 'surrogateescape') if len(lines) >= 1 else ""
    s2 = lines[1].decode('utf-8', 'surrogateescape') if len(lines) >= 2 else ""
    print(lcs_length(s1, s2))


if __name__ == '__main__':
    main()
