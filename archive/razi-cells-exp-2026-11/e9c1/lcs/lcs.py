import sys

def lcs(a: str, b: str) -> int:
    na = len(a)
    nb = len(b)
    if na == 0 or nb == 0:
        return 0
    # Strip common prefix
    start = 0
    limit = na if na < nb else nb
    while start < limit and a[start] == b[start]:
        start += 1
    if start == limit:
        return limit
    # Strip common suffix
    end_a = na
    end_b = nb
    while end_a > start and end_b > start and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1
    common = start + (na - end_a)
    a = a[start:end_a]
    b = b[start:end_b]
    if not a or not b:
        return common
    if len(a) > len(b):
        a, b = b, a
    m = len(a)
    pos = {}
    for i, ch in enumerate(a):
        pos[ch] = pos.get(ch, 0) | (1 << i)
    mask = (1 << m) - 1
    S = mask
    get_pos = pos.get
    for ch in b:
        P = get_pos(ch, 0)
        if P:
            u = S & P
            S = ((S + u) | (S - u)) & mask
    return common + (m - S.bit_count())

def main():
    data = sys.stdin.read().splitlines()
    if not data:
        print(0)
        return
    a = data[0]
    b = data[1] if len(data) > 1 else ""
    print(lcs(a, b))

if __name__ == "__main__":
    main()
