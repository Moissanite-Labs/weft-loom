import random, json, sys
sys.path.insert(0, '.')
from squeeze import compress, decompress
r = random.Random(1)
w = "the of and a to in is you that it he was for on are as with his they at be this from have or by one had not but what all were when we there can an your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know".split()
t = " ".join(r.choice(w) for _ in range(60000)).encode()
j = json.dumps([{"id": i, "name": r.choice(w), "tags": [r.choice(w) for _ in range(3)], "score": r.random(), "active": i % 2 == 0} for i in range(3000)]).encode()
d = t + j
c = compress(d)
assert decompress(c) == d
print(len(d) / len(c))
