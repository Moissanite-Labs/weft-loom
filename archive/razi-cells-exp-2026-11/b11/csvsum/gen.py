import random, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000000
random.seed(42)
cats = ["alpha","beta","gamma","delta","eps","zeta","eta","theta","iota","kappa","lambda","mu"]
out = sys.stdout
w = out.write
w("id,cat,val\n")
lines = []
for i in range(n):
    lines.append(f"{i},{random.choice(cats)},{random.randint(-100000,100000)/100:.2f}\n")
    if len(lines) >= 100000:
        w("".join(lines)); lines = []
w("".join(lines))
