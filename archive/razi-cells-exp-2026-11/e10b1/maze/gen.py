import sys, random
def gen(n, m, seed, dots=2):
    r = random.Random(seed)
    g = bytearray(r.choices(b'#' + b'.' * dots, k=n*m))
    g[0] = ord('S'); g[n*m-1] = ord('E')
    return '\n'.join(g[i*m:(i+1)*m].decode() for i in range(n)) + '\n'
if __name__ == '__main__':
    n = int(sys.argv[1]); m = int(sys.argv[2]); seed = int(sys.argv[3])
    dots = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    sys.stdout.write(gen(n, m, seed, dots))
