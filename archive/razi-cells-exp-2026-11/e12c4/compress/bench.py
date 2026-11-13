import random,json,time
from squeeze import compress,decompress
random.seed(1)
w=[''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(2,9))) for _ in range(800)]
t=' '.join(random.choice(w) for _ in range(40000))
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"v":random.random()} for i in range(1500)])
d=(t+j).encode()
c=compress(d)
assert decompress(c)==d
assert decompress(compress(b''))==b''
print(len(d)/len(c))
