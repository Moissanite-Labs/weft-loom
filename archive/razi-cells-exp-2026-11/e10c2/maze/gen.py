import sys, random
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
p = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
rnd = random.Random(seed)
out = []
for i in range(n):
    row = bytearray(35 if rnd.random() < p else 46 for _ in range(n))
    out.append(row)
out[0][0] = ord('S')
out[n-1][n-1] = ord('E')
sys.stdout.buffer.write(b'\n'.join(bytes(r) for r in out) + b'\n')
