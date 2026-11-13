import sys, random

random.seed(42)
cats = [f"cat_{i:02d}" for i in range(50)]
lines = ["id,cat,val\n"]
# generate a chunk of 10,000 rows and repeat/perturb or generate 2,000,000 rows fast
chunk = []
for i in range(20000):
    c = cats[i % 50]
    v = f"{(i * 17 % 100000) / 100.0:.2f}"
    chunk.append(f"{i},{c},{v}\n")
block = "".join(chunk)
with open("data.csv", "w") as f:
    f.write("id,cat,val\n")
    for _ in range(100):
        f.write(block)
