import sys

def lcs_length(a: str, b: str) -> int:
    if a == b:
        return len(a)
    # Strip common prefix and suffix
    na, nb = len(a), len(b)
    start = 0
    min_len = na if na < nb else nb
    while start < min_len and a[start] == b[start]:
        start += 1
    if start == min_len:
        return min_len
    end_a, end_b = na, nb
    while end_a > start and end_b > start and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1
    common = start + (na - end_a)
    a = a[start:end_a]
    b = b[start:end_b]
    if not a or not b:
        return common

    if len(a) < len(b):
        a, b = b, a

    pos = {}
    for i, ch in enumerate(b):
        pos[ch] = pos.get(ch, 0) | (1 << i)

    mask = (1 << len(b)) - 1
    S = mask
    get = pos.get
    for ch in a:
        P = get(ch, 0)
        if P:
            u = S & P
            S = (S + u) | (S - u)
    return common + ((~S) & mask).bit_count()

def main():
    lines = sys.stdin.read().splitlines()
    if len(lines) < 2:
        a = lines[0] if lines else ""
        b = ""
    else:
        a, b = lines[0], lines[1]
    print(lcs_length(a, b))

if __name__ == "__main__":
    main()
