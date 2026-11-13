import sys, random
N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 12345
density = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
rnd = random.Random(seed)
out = []
for i in range(N):
    row = bytearray(46 if rnd.random() >= density else 35 for _ in range(N))
    out.append(row)
out[0][0] = 83   # S
out[N-1][N-1] = 69  # E
sys.stdout.buffer.write(b'\n'.join(bytes(r) for r in out) + b'\n')
