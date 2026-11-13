import random, sys
def gen(n=2000, m=2000, seed=12345, p=0.3, out='big.txt', clear=3):
    r = random.Random(seed)
    rows = [bytearray(35 if r.random() < p else 46 for _ in range(m)) for _ in range(n)]
    for i in range(min(clear, n)):
        for j in range(min(clear, m)):
            rows[i][j] = 46; rows[n-1-i][m-1-j] = 46
    rows[0][0] = ord('S'); rows[n-1][m-1] = ord('E')
    with open(out, 'wb') as f:
        for row in rows:
            f.write(row + b'\n')
if __name__ == '__main__':
    a = sys.argv
    gen(int(a[1]), int(a[2]), int(a[3]), float(a[4]), a[5], int(a[6]) if len(a) > 6 else 3)
