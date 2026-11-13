import sys

def lcs(a, b):
    n = len(a)
    if n == 0 or len(b) == 0:
        return 0
    pm = {}
    for i, c in enumerate(a):
        pm[c] = pm.get(c, 0) | (1 << i)
    mask = (1 << n) - 1
    V = mask
    get = pm.get
    for c in b:
        U = V & get(c, 0)
        V = ((V + U) | (V - U)) & mask
    return n - bin(V).count('1')

def main():
    data = sys.stdin.read().split('\n')
    a = data[0] if len(data) > 0 else ''
    b = data[1] if len(data) > 1 else ''
    print(lcs(a, b))

if __name__ == '__main__':
    main()
