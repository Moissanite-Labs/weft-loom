import random,sys
n=int(sys.argv[1]);r=random.Random(7)
g=[['#' if r.random()<0.25 else '.' for _ in range(n)] for _ in range(n)]
g[0][1]=g[1][0]=g[-1][-2]=g[-2][-1]='.'
g[0][0]='S';g[-1][-1]='E'
print('\n'.join(''.join(x) for x in g))
