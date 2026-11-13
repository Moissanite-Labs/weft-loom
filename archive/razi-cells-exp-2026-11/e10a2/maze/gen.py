import random, sys
def gen(n, m, seed, p=0.3):
    r = random.Random(seed)
    rows = []
    for i in range(n):
        rows.append(''.join('#' if r.random() < p else '.' for _ in range(m)))
    g = [list(x) for x in rows]
    g[0][0] = 'S'; g[n-1][m-1] = 'E'
    return '\n'.join(''.join(x) for x in g) + '\n'
if __name__ == '__main__':
    n = int(sys.argv[1]); m = int(sys.argv[2]); seed = int(sys.argv[3])
    p = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    sys.stdout.write(gen(n, m, seed, p))
