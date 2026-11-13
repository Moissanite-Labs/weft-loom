import sys

def lcs(a, b):
    if len(a) < len(b):
        a, b = b, a
    n = len(a)
    if n == 0 or not b:
        return 0
    masks = {}
    for i, c in enumerate(a):
        masks[c] = masks.get(c, 0) | (1 << i)
    S = 0
    get = masks.get
    for c in b:
        x = S | get(c, 0)
        S = x & ~(x - ((S << 1) | 1))
    return bin(S).count('1')

def main():
    data = sys.stdin.read().split('\n')
    a = data[0] if len(data) > 0 else ''
    b = data[1] if len(data) > 1 else ''
    print(lcs(a, b))

if __name__ == '__main__':
    main()
