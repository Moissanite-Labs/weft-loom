import random, json, time
import squeeze
random.seed(1)
w = ["the","of","and","data","system","quick","brown","fox","jumps","over","lazy","dog","compression","value","name","time","user","report"]
t = " ".join(random.choice(w) for _ in range(60000)).encode()
j = json.dumps([{"id":i,"name":random.choice(w),"score":random.random(),"tags":random.sample(w,3)} for i in range(3000)]).encode()
d = t + j
c = squeeze.compress(d)
print(len(d)/len(c) if squeeze.decompress(c) == d else 0)
