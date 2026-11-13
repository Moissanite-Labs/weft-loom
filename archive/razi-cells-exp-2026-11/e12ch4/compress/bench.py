import random,json,sys
sys.path.insert(0,'.')
import squeeze
random.seed(1)
w=("the of and to in is that it was for on are as with his they at be this from have or by one had not but what all were when we there can an your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know".split())
t=" ".join(random.choice(w) for _ in range(60000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"score":random.random(),"active":i%3==0} for i in range(4000)]).encode()
d=t+j
c=squeeze.compress(d)
ok=squeeze.decompress(c)==d
print(len(d)/len(c) if ok else 0)
