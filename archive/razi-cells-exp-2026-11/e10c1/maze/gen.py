import sys, random
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
random.seed(seed)
rows = []
for r in range(n):
    rows.append(''.join('#' if random.random() < 0.3 else '.' for _ in range(n)))
g = [list(x) for x in rows]
g[0][0] = 'S'
g[n-1][n-1] = 'E'
sys.stdout.write('\n'.join(''.join(x) for x in g) + '\n')
