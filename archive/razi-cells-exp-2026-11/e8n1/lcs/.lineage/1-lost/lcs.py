import sys

def lcs_length(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return len(a)
    
    la, lb = len(a), len(b)
    # Trim common prefix
    start = 0
    min_len = la if la < lb else lb
    while start < min_len and a[start] == b[start]:
        start += 1
    if start == min_len:
        return min_len
    
    # Trim common suffix
    end_a, end_b = la - 1, lb - 1
    while end_a >= start and end_b >= start and a[end_a] == b[end_b]:
        end_a -= 1
        end_b -= 1
    
    a = a[start:end_a + 1]
    b = b[start:end_b + 1]
    trimmed = start + (la - 1 - end_a)
    
    if not a or not b:
        return trimmed
    
    if len(a) > len(b):
        a, b = b, a
    
    pos = {}
    for i, ch in enumerate(a):
        pos[ch] = pos.get(ch, 0) | (1 << i)
    
    mask = (1 << len(a)) - 1
    S = mask
    for ch in b:
        pm = pos.get(ch, 0)
        if pm:
            u = S & pm
            S = ((S + u) | (S - u)) & mask
            
    return trimmed + (len(a) - S.bit_count())

def main():
    data = sys.stdin.read().splitlines()
    if len(data) < 2:
        a = data[0] if len(data) >= 1 else ""
        b = ""
    else:
        a, b = data[0], data[1]
    print(lcs_length(a, b))

if __name__ == "__main__":
    main()
