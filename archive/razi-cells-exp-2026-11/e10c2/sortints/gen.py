import random, sys
random.seed(12345)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000
r = random.Random(12345)
sys.stdout.write("\n".join(str(r.randint(-2**31, 2**31)) for _ in range(n)) + "\n")
