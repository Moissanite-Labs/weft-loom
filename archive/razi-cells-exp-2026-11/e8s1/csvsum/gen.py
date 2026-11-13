import random, sys

random.seed(42)
cats = [f"cat_{i:02d}" for i in range(50)]
# Pre-build chunks for fast generation
lines = []
sums = {c: 0.0 for c in cats}
# Let us generate 2,000,000 rows fast
import numpy as np
rng = np.random.default_rng(42)
N = 2000000
cat_idx = rng.integers(0, 50, size=N)
vals = np.round(rng.uniform(-1000.0, 10000.0, size=N), 2)

# compute exact expected sums
with open("expected.txt", "w") as f:
    for i, c in enumerate(cats):
        s = vals[cat_idx == i].sum()
        f.write(f"{c},{s:.2f}\n")

# write test.csv fast in chunks
with open("test.csv", "w", buffering=1024*1024*8) as f:
    f.write("id,cat,val\n")
    chunk = 100000
    for start in range(0, N, chunk):
        end = start + chunk
        c_sub = cat_idx[start:end]
        v_sub = vals[start:end]
        lines = [f"{ id_ },{cats[c]},{v:.2f}\n" for id_, c, v in zip(range(start, end), c_sub, v_sub)]
        f.write("".join(lines))
print("Generated test.csv and expected.txt")
