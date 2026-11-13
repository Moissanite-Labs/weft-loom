import random, json, sys
from squeeze import compress, decompress
r = random.Random(1)
w = "the quick brown fox jumps over lazy dog while time and tide wait for no man of letters".split() + ["compression", "ratio", "stream", "model", "entropy"]
text = " ".join(r.choice(w) for _ in range(60000)).encode()
js = json.dumps([{"id": i, "name": r.choice(w), "tags": [r.choice(w) for _ in range(3)], "v": r.random()} for i in range(3000)]).encode()
tot = n = 0
for d in (text, js):
    c = compress(d)
    if decompress(c) != d:
        print(0); sys.exit()
    tot += len(d); n += len(c)
print(tot / n)
