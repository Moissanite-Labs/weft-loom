import random
n=2000
r=random.Random(7)
rows=[bytearray(''.join('#' if r.random()<0.28 else '.' for _ in range(n)),'ascii') for _ in range(n)]
for i in range(3):
    for j in range(3):
        rows[i][j]=46; rows[n-1-i][n-1-j]=46
rows[0][0]=83; rows[-1][-1]=69
print('\n'.join(x.decode() for x in rows))
