import random, json
import squeeze
random.seed(1)
w = "the quick brown fox jumps over lazy dog while time and tide wait for no man about science history river stone light".split()
t = " ".join(random.choice(w) for _ in range(60000)).encode()
j = json.dumps([{"id": i, "name": random.choice(w), "tags": [random.choice(w) for _ in range(3)], "v": random.random()} for i in range(3000)]).encode()
tot = out = 0
for d in (t, j):
    c = squeeze.compress(d)
    if squeeze.decompress(c) != d:
        print(0); raise SystemExit
    tot += len(d); out += len(c)
print(tot / out)
