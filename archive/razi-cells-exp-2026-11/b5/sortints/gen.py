import random
random.seed(12345)
n=1000000
print(" ".join(str(random.randint(-2**31,2**31)) for _ in range(n)))
