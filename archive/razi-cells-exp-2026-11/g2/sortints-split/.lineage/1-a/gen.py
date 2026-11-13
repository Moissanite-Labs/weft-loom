import random, sys
n = int(sys.argv[1]) if len(sys.argv)>1 else 1000000
seed = int(sys.argv[2]) if len(sys.argv)>2 else 12345
out = sys.argv[3] if len(sys.argv)>3 else 'data.txt'
r = random.Random(seed)
with open(out, 'w') as f:
    for _ in range(n):
        f.write(str(r.randint(-10**9, 10**9)))
        f.write('\n')
