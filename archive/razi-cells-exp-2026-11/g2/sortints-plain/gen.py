import random, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000
random.seed(42)
with open('test_1m.txt', 'w') as f:
    f.write('\n'.join(str(random.randint(-10**9, 10**9)) for _ in range(n)))
    f.write('\n')
