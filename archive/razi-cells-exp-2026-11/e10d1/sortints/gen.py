import random, sys
random.seed(12345)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000
out = []
for i in range(n):
    out.append(str(random.randint(-10**9, 10**9)))
    out.append(" " if random.random() < 0.9 else "\n")
sys.stdout.write("".join(out))
