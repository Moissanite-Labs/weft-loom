import random,json,squeeze
random.seed(1)
w="the of and to in is that it was for on are as with his they at be this from have or by one had not but what all were when we there can an your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know".split()
t=" ".join(random.choice(w) for _ in range(150000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"v":random.random()} for i in range(3000)]).encode()
d=t+j
c=squeeze.compress(d)
print(len(d)/len(c) if squeeze.decompress(c)==d else 0)
