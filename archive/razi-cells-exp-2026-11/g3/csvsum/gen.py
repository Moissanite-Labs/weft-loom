import random, sys

random.seed(1234)
cats = [("cat%03d" % i) for i in range(500)]
cents = {}
with open("data.csv", "w", newline="\n") as f:
    f.write("id,cat,val\n")
    out = []
    for i in range(2000000):
        c = cats[i % 500] if i % 3 else random.choice(cats)
        v = random.randrange(0, 100000)  # cents 0..999.99
        cents[c] = cents.get(c, 0) + v
        out.append("%d,%s,%d.%02d\n" % (i, c, v // 100, v % 100))
        if len(out) >= 10000:
            f.write("".join(out))
            out = []
    f.write("".join(out))

with open("expected.txt", "w") as f:
    for c in sorted(cents):
        v = cents[c]
        sign = "-" if v < 0 else ""
        v = abs(v)
        f.write("%s %s%d.%02d\n" % (c, sign, v // 100, v % 100))
print("ok")
