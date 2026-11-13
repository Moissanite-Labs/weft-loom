import random, sys
random.seed(12345)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000
out = []
for _ in range(n):
    out.append(str(random.randint(-2**31, 2**31 - 1)))
sys.stdout.write(" ".join(out) + "\n")
