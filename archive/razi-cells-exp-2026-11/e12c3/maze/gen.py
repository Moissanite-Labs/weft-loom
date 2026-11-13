import random
random.seed(1)
n=2000
g=[['#']*n for _ in range(n)]
for i in range(n):
    for j in range(n):
        if random.random()<0.7: g[i][j]='.'
g[0][1]=g[1][0]=g[n-1][n-2]=g[n-2][n-1]='.'
g[0][0]='S';g[n-1][n-1]='E'
print('\n'.join(''.join(r) for r in g))
