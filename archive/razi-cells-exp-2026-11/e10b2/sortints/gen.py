import random
random.seed(12345)
n=1000000
with open('data.txt','w') as f:
    f.write('\n'.join(str(random.randint(-2**31,2**31-1)) for _ in range(n)))
    f.write('\n')
