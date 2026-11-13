import random
n=2000
r=random.Random(7)
rows=[bytearray(''.join('#' if r.random()<0.28 else '.' for _ in range(n)),'ascii') for _ in range(n)]
rows[0][0:3]=b'S..'; rows[1][0:2]=b'..'
rows[-1][-3:]=b'..E'; rows[-2][-2:]=b'..'
print('\n'.join(x.decode() for x in rows))
