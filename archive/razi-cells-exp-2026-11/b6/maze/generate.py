import random
n=2000
rng=random.Random(314159)
table=bytes(35 if i<64 else 46 for i in range(256))
rows=[bytearray(rng.randbytes(n).translate(table)) for _ in range(n)]
# A guaranteed route of Manhattan length, plus a large random reachable interior.
rows[0][:]=b'.'*n
for row in rows: row[-1]=46
rows[0][0]=83; rows[-1][-1]=69
with open('large.txt','wb') as f: f.write(b'\n'.join(rows)+b'\n')
print('Expected shortest length:',2*(n-1))
