import random, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
random.seed(42)
cats = ["cat%02d" % i for i in range(50)]
out = sys.stdout
out.write("id,cat,val\n")
w = out.write
rc = random.choice; ru = random.uniform
lines = []
for i in range(n):
    lines.append("%d,%s,%.2f\n" % (i, rc(cats), ru(-1000, 1000)))
    if len(lines) >= 100000:
        w("".join(lines)); lines = []
w("".join(lines))
