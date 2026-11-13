import random,json,squeeze
random.seed(1)
w=["the","of","and","data","time","system","info","value","name","user","list","quick","brown","fox","over","lazy","dog","process","result","error"]
t=" ".join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"v":random.random(),"tags":random.sample(w,3)} for i in range(3000)]).encode()
d=t+j
c=squeeze.compress(d)
print(len(d)/len(c) if squeeze.decompress(c)==d else 0)
