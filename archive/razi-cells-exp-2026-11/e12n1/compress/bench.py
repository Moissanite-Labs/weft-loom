import random, json, sys
import squeeze
r = random.Random(1)
w = "the quick brown fox jumps over a lazy dog while time and tide wait for no one in the old house".split()
t = " ".join(r.choice(w) for _ in range(150000)).encode()
j = json.dumps([{"id": i, "name": r.choice(w), "tags": [r.choice(w) for _ in range(3)], "v": r.random()} for i in range(5000)]).encode()
d = t + j
c = squeeze.compress(d)
if squeeze.decompress(c) != d:
    print(0); sys.exit()
print(len(d) / len(c))
