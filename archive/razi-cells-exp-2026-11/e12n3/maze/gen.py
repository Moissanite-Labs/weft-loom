import random
random.seed(7)
n=2000
rows=[[('#' if random.random()<0.3 else '.') for _ in range(n)] for _ in range(n)]
for i in range(3):
    for j in range(3):
        rows[i][j]='.'; rows[n-1-i][n-1-j]='.'
rows[0][0]='S';rows[-1][-1]='E'
open('maze.txt','w').write("\n".join("".join(r) for r in rows)+"\n")
