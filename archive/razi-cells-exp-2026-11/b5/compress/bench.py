import random, json, sys, importlib
sys.path.insert(0, ".")
sq = importlib.import_module("squeeze")

def gen():
    r = random.Random(12345)
    words = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split())
    words += ["".join(r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(r.randint(3, 10))) for _ in range(400)]
    text = []
    for _ in range(40000):
        w = r.choice(words)
        if r.random() < 0.08: w = w.capitalize()
        text.append(w)
        if r.random() < 0.07: text[-1] += r.choice([".", ",", ";", "!", "?"])
        if r.random() < 0.02: text.append("\n")
    txt = " ".join(text).encode()
    recs = []
    for i in range(3000):
        recs.append({"id": i, "name": r.choice(words), "email": r.choice(words) + "@example.com",
                     "active": r.random() < 0.5, "score": round(r.random() * 100, 3),
                     "tags": [r.choice(words) for _ in range(r.randint(0, 4))],
                     "address": {"city": r.choice(words).title(), "zip": r.randint(10000, 99999)}})
    js = json.dumps(recs, indent=2).encode()
    return [txt, js, txt[:5000] + js[:5000]]

total_in = total_out = 0
for d in gen():
    c = sq.compress(d)
    if sq.decompress(c) != d:
        print(0); sys.exit(1)
    total_in += len(d); total_out += len(c)
print(round(total_in / total_out, 4))
