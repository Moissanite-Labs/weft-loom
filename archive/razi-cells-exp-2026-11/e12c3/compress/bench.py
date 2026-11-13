import random,json,sys
import squeeze
random.seed(1)
w=["the","of","and","time","people","system","data","value","north","river","quick","brown","fox","lazy","dog","over","under","with","language","model"]
t=" ".join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":random.sample(w,3),"score":random.random()} for i in range(3000)]).encode()
d=t+j
c=squeeze.compress(d)
if squeeze.decompress(c)!=d: print(0);sys.exit()
print(len(d)/len(c))
