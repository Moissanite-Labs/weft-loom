import random
random.seed(7)
n=2000
r=[''.join('#' if random.random()<0.25 else '.' for _ in range(n)) for _ in range(n)]
r[0]='S'+r[0][1:]; r[-1]=r[-1][:-1]+'E'
open('big.txt','w').write('\n'.join(r)+'\n')
