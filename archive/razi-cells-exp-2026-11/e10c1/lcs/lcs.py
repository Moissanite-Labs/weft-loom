import sys

def lcs_len(a, b):
    n = len(a)
    if n == 0 or len(b) == 0:
        return 0
    M = {}
    for i, c in enumerate(a):
        M[c] = M.get(c, 0) | (1 << i)
    mask = (1 << n) - 1
    V = mask
    get = M.get
    for k in range(0, len(b), 64):
        for c in b[k:k+64]:
            U = V & get(c, 0)
            V = (V + U) | (V ^ U)
        V &= mask
    return n - bin(V).count("1")

def main():
    data = sys.stdin.read().split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    print(lcs_len(a, b))

if __name__ == "__main__":
    main()
