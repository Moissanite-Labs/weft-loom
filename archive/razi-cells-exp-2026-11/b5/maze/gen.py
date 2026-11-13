import random, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
random.seed(12345)
rows = []
for r in range(n):
    rows.append(''.join('#' if random.random() < 0.25 else '.' for _ in range(n)))
g = [list(r) for r in rows]
g[0][0] = 'S'; g[n-1][n-1] = 'E'
sys.stdout.write('\n'.join(''.join(r) for r in g) + '\n')
