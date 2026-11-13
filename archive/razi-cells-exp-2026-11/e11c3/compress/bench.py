import random, json, time
import squeeze
random.seed(1)
w = "the of and to in is that it was for on are with as his they be at one have this from or had by word but not what all were we when your can said there use an each which she do how their if will up other about out many then them these so some her would make like him into time has look two more write go see number no way could people my than first water been call who oil its now find long down day did get come made may part".split()
t = []
for i in range(6000):
    t.append(random.choice(w))
txt = " ".join(t).encode()
js = json.dumps([{"id": i, "name": random.choice(w) + str(random.randint(0, 99)), "tags": random.sample(w, 3), "v": random.random()} for i in range(2500)]).encode()
d = txt + js
c = squeeze.compress(d)
assert squeeze.decompress(c) == d
print(len(d) / len(c))
