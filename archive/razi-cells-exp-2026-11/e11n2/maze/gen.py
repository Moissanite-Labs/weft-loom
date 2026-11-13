import random
random.seed(7)
n=2000
g=[['#' if random.random()<0.3 else '.' for _ in range(n)] for _ in range(n)]
g[0][1]=g[1][0]=g[-1][-2]=g[-2][-1]='.'
g[0][0]='S';g[-1][-1]='E'
print("\n".join("".join(r) for r in g))
