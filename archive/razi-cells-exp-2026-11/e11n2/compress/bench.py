import random,json,time
from squeeze import compress,decompress
random.seed(1)
w=("the of and to in is that it was for on are with as his they be at one have this from or had by word but what some we can out other were all there when up use your how said an each she which do their time if will way about many then them write would like so these her long make thing see him two has look more day could go come did number sound no most people my over know water than call first who may down side been now find".split())
t=" ".join(random.choice(w) for _ in range(150000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"score":random.random()} for i in range(4000)]).encode()
d=t+j
c=compress(d)
print(len(d)/len(c) if decompress(c)==d else 0)
