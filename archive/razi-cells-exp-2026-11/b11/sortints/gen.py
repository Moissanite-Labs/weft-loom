import random
random.seed(12345)
r=random.Random(12345)
print(' '.join(str(r.randint(-2**31, 2**31)) for _ in range(1000000)))
