import sys


def lcs_length(a: str, b: str) -> int:
    """Return the length of the longest common subsequence of a and b."""
    if not a or not b:
        return 0

    # Use the shorter string for the outer loop (fewer big-int operations).
    if len(a) > len(b):
        a, b = b, a

    # match[ch] has bit i set iff b[i] == ch.
    match = {}
    for i, ch in enumerate(b):
        match[ch] = match.get(ch, 0) | (1 << i)

    mask = (1 << len(b)) - 1
    S = 0
    get = match.get
    for ch in a:
        m = get(ch, 0)
        x = S | m
        y = (S << 1) | 1
        S = (x & ~(x - y)) & mask

    try:
        return S.bit_count()
    except AttributeError:
        return bin(S).count("1")


def main() -> None:
    data = sys.stdin.read().splitlines()
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    print(lcs_length(a, b))


if __name__ == "__main__":
    main()
