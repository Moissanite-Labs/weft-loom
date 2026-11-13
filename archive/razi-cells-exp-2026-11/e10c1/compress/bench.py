import random, json, sys, importlib
random.seed(12345)
WORDS = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split()
         + ["compression","algorithm","dictionary","entropy","sentence","paragraph","function","variable","network","system","quickly","because","however","therefore","between","another","through","example","language","python"])
def text(n):
    out=[]
    while len(out) < n:
        s = [random.choice(WORDS) for _ in range(random.randint(5, 18))]
        s[0] = s[0].capitalize()
        out.append(" ".join(s) + random.choice([". ", ". ", "? ", "! ", ".\n"]))
    return "".join(out)
def jsonb(n):
    recs=[]
    for i in range(n):
        recs.append({"id": i, "name": random.choice(WORDS)+str(random.randint(1,999)),
                     "email": random.choice(WORDS)+"@example.com", "active": random.random()<0.5,
                     "score": round(random.random()*100, 3),
                     "tags": [random.choice(WORDS) for _ in range(random.randint(0,5))],
                     "address": {"city": random.choice(WORDS).title(), "zip": "%05d" % random.randint(0,99999)}})
    return json.dumps(recs, indent=2)
chunks = []
for k in range(6):
    chunks.append(text(400).encode())
    chunks.append(jsonb(300).encode())
chunks.append(b"")
chunks.append(b"x")
chunks.append(bytes(range(256))*4)
sys.path.insert(0, ".")
sq = importlib.import_module("squeeze")
tot_in = tot_out = 0
for c in chunks:
    b = sq.compress(c)
    if sq.decompress(b) != c:
        print(0); sys.exit(0)
    tot_in += len(c); tot_out += len(b)
print(tot_in / tot_out)
