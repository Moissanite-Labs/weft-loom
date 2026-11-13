import random, json, sys, time
import squeeze

def gen():
    r = random.Random(12345)
    words = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split()
             + ["compression","algorithm","dictionary","entropy","network","python","function","variable","system","data","model","process","result","value","string","number","object","request","response","server","client","user","message","error","status"])
    out = []
    # English-like text ~400KB
    for _ in range(6000):
        n = r.randint(6, 18)
        s = " ".join(r.choice(words) for _ in range(n))
        out.append(s[0].upper() + s[1:] + r.choice([". ", ". ", "? ", "! ", ".\n"]))
    text = "".join(out).encode()
    # JSON ~400KB
    recs = []
    for i in range(3000):
        recs.append({"id": i, "name": r.choice(words) + "_" + str(r.randint(0, 999)),
                     "email": r.choice(words) + "@example.com", "active": r.random() > 0.3,
                     "score": round(r.random() * 100, 3), "tags": [r.choice(words) for _ in range(r.randint(0, 5))],
                     "address": {"city": r.choice(words).title(), "zip": "%05d" % r.randint(0, 99999)},
                     "ts": "2024-%02d-%02dT%02d:%02d:%02dZ" % (r.randint(1, 12), r.randint(1, 28), r.randint(0, 23), r.randint(0, 59), r.randint(0, 59))})
    js = json.dumps(recs, indent=2).encode()
    js2 = json.dumps(recs[:1000]).encode()
    return [text, js, js2, text[:5000], js2[:3000]]

def main():
    inputs = gen()
    total_in = total_out = 0
    t0 = time.time()
    for d in inputs:
        c = squeeze.compress(d)
        if squeeze.decompress(c) != d:
            print(0); return
        total_in += len(d); total_out += len(c)
    if squeeze.decompress(squeeze.compress(b"")) != b"":
        print(0); return
    print("%.4f" % (total_in / total_out))
    print("time %.2fs in=%d out=%d" % (time.time() - t0, total_in, total_out), file=sys.stderr)

main()
