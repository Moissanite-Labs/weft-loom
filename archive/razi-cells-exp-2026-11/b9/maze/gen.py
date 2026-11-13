import sys, random
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 12345
random.seed(seed)
rows = []
for r in range(n):
    rows.append(''.join('#' if random.random() < 0.3 else '.' for _ in range(n)))
rows[0] = 'S' + rows[0][1:]
rows[-1] = rows[-1][:-1] + 'E'
sys.stdout.write('\n'.join(rows) + '\n')
