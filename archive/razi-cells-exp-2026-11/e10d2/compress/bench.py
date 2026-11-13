import random, json, sys, time
import squeeze

def gen():
    r = random.Random(12345)
    words = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split()
             + ["".join(r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(r.randint(3, 10))) for _ in range(1500)])
    parts = []
    for _ in range(6000):
        n = r.randint(5, 20)
        s = " ".join(r.choice(words) for _ in range(n))
        parts.append(s[0].upper() + s[1:] + r.choice([".", ".", "!", "?"]))
    text = " ".join(parts).encode()
    keys = ["id", "name", "email", "age", "active", "tags", "score", "address", "city", "zip", "created", "notes"]
    recs = []
    for i in range(5000):
        recs.append({"id": i, "name": r.choice(words) + " " + r.choice(words), "email": r.choice(words) + "@example.com",
                     "age": r.randint(18, 90), "active": r.random() < 0.5,
                     "tags": [r.choice(words) for _ in range(r.randint(0, 4))], "score": round(r.random() * 100, 2),
                     "address": {"city": r.choice(words), "zip": "%05d" % r.randint(0, 99999)},
                     "created": "2023-%02d-%02dT%02d:%02d:00Z" % (r.randint(1, 12), r.randint(1, 28), r.randint(0, 23), r.randint(0, 59)),
                     "notes": " ".join(r.choice(words) for _ in range(r.randint(0, 12)))})
    js = json.dumps(recs, indent=2).encode()
    return [text, js, text[:50000] + js[:50000], b"", b"x" * 1000]

def main():
    total_in = total_out = 0
    for d in gen():
        c = squeeze.compress(d)
        if squeeze.decompress(c) != d:
            print(0); sys.exit(1)
        total_in += len(d); total_out += len(c)
    print("%.4f" % (total_in / total_out))

if __name__ == "__main__":
    main()
