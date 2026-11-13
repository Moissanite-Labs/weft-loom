import random,json,time
from squeeze import compress,decompress
random.seed(1)
w=["the","of","and","data","system","compress","time","market","river","quick","brown","fox","value","name","report","light","street","modern","history","people"]
t=" ".join(random.choice(w)+random.choice(["",",","."]) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":random.sample(w,3),"score":random.random()} for i in range(3000)]).encode()
d=t+j
c=compress(d)
assert decompress(c)==d
print(len(d)/len(c))
