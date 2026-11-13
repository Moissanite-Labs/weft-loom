import random
random.seed(12345)
with open('data.txt','w') as f:
    f.write('\n'.join(str(random.randint(-10**9,10**9)) for _ in range(1000000))+'\n')
