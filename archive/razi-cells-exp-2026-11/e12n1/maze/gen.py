import random
random.seed(1)
n=2000
rows=[''.join('#' if random.random()<0.3 else '.' for _ in range(n)) for _ in range(n)]
rows[0]='S'+rows[0][1:]
rows[-1]=rows[-1][:-1]+'E'
open('maze.txt','w').write('\n'.join(rows)+'\n')
