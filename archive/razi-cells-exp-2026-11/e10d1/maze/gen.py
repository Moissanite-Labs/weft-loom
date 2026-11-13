import sys, numpy as np
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
p = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
rng = np.random.default_rng(seed)
g = np.where(rng.random((n, n)) < p, ord('#'), ord('.')).astype(np.uint8)
g[0, 0] = ord('S'); g[n-1, n-1] = ord('E')
out = np.full((n, n+1), ord('\n'), dtype=np.uint8)
out[:, :n] = g
sys.stdout.buffer.write(out.tobytes())
