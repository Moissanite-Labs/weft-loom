import random
random.seed(7)
n=2000
rows=[]
for i in range(n):
    rows.append(''.join('#' if random.random()<0.2 else '.' for _ in range(n)))
rows[0]='S.'+rows[0][2:]
rows[1]='.'+rows[1][1:]
rows[-1]=rows[-1][:-2]+'.E'
rows[-2]=rows[-2][:-1]+'.'
rows[0]='S'+rows[0][1:]
rows[-1]=rows[-1][:-1]+'E'
open('big.txt','w').write('\n'.join(rows)+'\n')
