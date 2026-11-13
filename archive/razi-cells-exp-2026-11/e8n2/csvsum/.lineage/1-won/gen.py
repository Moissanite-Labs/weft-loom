import random, os

random.seed(42)
cats = [f"cat_{i:02d}" for i in range(25)]
# Generate 2,000,000 rows fast
chunk = []
sums = {c: 0 for c in cats} # in cents to avoid float drift in reference
for i in range(2000):
    c = cats[i % 25]
    v_cents = random.randint(-10000, 100000)
    sums[c] += v_cents * 1000
    chunk.append(f"{i},{c},{v_cents/100:.2f}\n")
block = "".join(chunk)
with open("data.csv", "w") as f:
    f.write("id,cat,val\n")
    for _ in range(1000):
        f.write(block)

with open("expected.txt", "w") as f:
    for c in sorted(cats):
        f.write(f"{c},{sums[c]/100:.2f}\n")
