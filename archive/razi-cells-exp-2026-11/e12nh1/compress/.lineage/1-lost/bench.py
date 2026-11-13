import random,json
import squeeze
random.seed(1)
w="the quick brown fox jumps over lazy dog while time and tide wait for no man in a very small town".split()
t=" ".join(random.choice(w) for _ in range(40000)).encode()
j=json.dumps([{"id":i,"name":random.choice(w),"tags":[random.choice(w) for _ in range(3)],"v":random.random()} for i in range(3000)]).encode()
d=t+j
c=squeeze.compress(d)
print(len(d)/len(c) if squeeze.decompress(c)==d else 0)
