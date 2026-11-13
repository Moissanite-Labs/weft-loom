import random,json,time
from squeeze import compress,decompress
random.seed(1)
w=[''.join(random.choice('abcdefghijklmnoprstuy') for _ in range(random.randint(2,9))) for _ in range(800)]
t=' '.join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"v":random.random()} for i in range(3000)]).encode()
d=t+j
c=compress(d)
print(len(d)/len(c) if decompress(c)==d else 0)
