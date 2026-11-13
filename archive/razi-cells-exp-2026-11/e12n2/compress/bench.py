import random, json, sys
import squeeze
random.seed(1)
w = "the of and to in is that for it as was with be by on not he this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split()
w += ["".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(random.randint(3,9))) for _ in range(400)]
text = " ".join(random.choice(w) for _ in range(120000)).encode()
recs = [{"id": i, "name": random.choice(w), "tags": random.sample(w, 3), "score": random.random(), "ok": i % 3 == 0} for i in range(6000)]
js = json.dumps(recs).encode()
tot = 0; comp = 0
for d in (text, js, b"", b"a"):
    c = squeeze.compress(d)
    if squeeze.decompress(c) != d:
        print(0); sys.exit()
    tot += len(d); comp += len(c)
print(tot / comp)
