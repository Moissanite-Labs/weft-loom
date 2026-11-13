import random,json,sys
sys.path.insert(0,'.')
import squeeze
random.seed(1)
w=["the","of","and","time","people","system","data","value","name","north","river","house","quick","brown","fox","over","lazy","dog"]
t=" ".join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":random.sample(w,3),"score":random.random()} for i in range(3000)]).encode()
d=t+j
c=squeeze.compress(d)
print(len(d)/len(c) if squeeze.decompress(c)==d else 0)
