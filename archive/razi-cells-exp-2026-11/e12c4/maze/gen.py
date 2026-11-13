import random
random.seed(7)
n=2000
g=[['#' if random.random()<0.25 else '.' for _ in range(n)] for _ in range(n)]
g[0][0]='S';g[n-1][n-1]='E'
open('m.txt','w').write('\n'.join(''.join(r) for r in g)+'\n')
