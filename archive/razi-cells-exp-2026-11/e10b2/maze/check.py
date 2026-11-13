import random
from gen import gen
from ref import ref
from maze import solve
r = random.Random(1)
bad = 0; neg = 0
for i in range(600):
    h = r.randint(1, 14); w = r.randint(1, 14)
    if h*w < 2: continue
    d = gen(h, w, i, r.choice([0.0, 0.2, 0.35, 0.5]))
    # random S/E placement
    b = bytearray(d.replace(b"S", b".").replace(b"E", b"."))
    cells = [k for k, c in enumerate(b) if c != 10]
    a, c = r.sample(cells, 2)
    b[a] = ord('S'); b[c] = ord('E')
    d = bytes(b)
    x, y = solve(d), ref(d)
    if y == -1: neg += 1
    if x != y:
        bad += 1
        if bad < 4: print("MISMATCH", x, y); print(d.decode())
print("bad", bad, "unreachable cases", neg)
