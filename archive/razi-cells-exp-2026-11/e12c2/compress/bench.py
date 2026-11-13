import random,json,squeeze
random.seed(1)
w=[''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(random.randint(2,9))) for _ in range(800)]
t=' '.join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"v":random.random()} for i in range(5000)]).encode()
d=t+j
c=squeeze.compress(d)
assert squeeze.decompress(c)==d
print(len(d)/len(c))
