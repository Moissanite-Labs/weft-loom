import random,json,time
from squeeze import compress,decompress
random.seed(1)
w=["the","of","and","time","data","system","quick","brown","fox","over","lazy","dog","compression","ratio","text","english","like","with","for","that"]
t=" ".join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"v":random.random()} for i in range(3000)]).encode()
d=t+j
c=compress(d)
assert decompress(c)==d
print(len(d)/len(c))
