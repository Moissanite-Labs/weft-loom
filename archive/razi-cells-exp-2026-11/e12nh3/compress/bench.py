import random, json, sys
sys.path.insert(0, '.')
import squeeze
random.seed(1)
w = "the quick brown fox jumps over lazy dog while time and tide wait for no man in a quiet town".split()
t = " ".join(random.choice(w) for _ in range(40000)).encode()
j = json.dumps([{"id": i, "name": random.choice(w), "tags": [random.choice(w) for _ in range(3)], "v": random.random()} for i in range(3000)]).encode()
d = t + j
c = squeeze.compress(d)
ok = squeeze.decompress(c) == d and squeeze.decompress(squeeze.compress(b"")) == b""
print(len(d) / len(c) if ok else 0)
