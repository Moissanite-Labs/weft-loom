import random, json, sys, time
import squeeze

def gen(seed=12345):
    r = random.Random(seed)
    words = ("the of and to in a is that for it as with was his he be not by but have you which are on or her had at from this "
             "there were been their one all we when who will more no if out so said what up its about into than them can only "
             "other new some could time these two may then do first any my now such like our over man me even most made after "
             "also did many before must through back years where much your way well down should because each just those people "
             "mr how too little state good very make world still own see men work long get here between both life being under "
             "never day same another know while last might us great old year off come since against go came right used take three").split()
    def sentence():
        n = r.randint(5, 18)
        ws = [r.choice(words) for _ in range(n)]
        ws[0] = ws[0].capitalize()
        return " ".join(ws) + r.choice([". ", ". ", ". ", "? ", "! ", ", "])
    def paragraph():
        return "".join(sentence() for _ in range(r.randint(3, 9))).strip() + "\n\n"
    text = "".join(paragraph() for _ in range(220))
    def rec(i):
        return {"id": i, "name": r.choice(words) + " " + r.choice(words),
                "email": r.choice(words) + str(r.randint(1, 999)) + "@example.com",
                "active": r.random() < 0.7, "score": round(r.random() * 100, 3),
                "tags": [r.choice(words) for _ in range(r.randint(0, 5))],
                "address": {"city": r.choice(words).title(), "zip": "%05d" % r.randint(0, 99999),
                            "geo": [round(r.uniform(-90, 90), 5), round(r.uniform(-180, 180), 5)]},
                "created": "2023-%02d-%02dT%02d:%02d:%02dZ" % (r.randint(1,12), r.randint(1,28), r.randint(0,23), r.randint(0,59), r.randint(0,59)),
                "notes": sentence().strip()}
    js = json.dumps([rec(i) for i in range(900)], indent=2)
    js2 = "\n".join(json.dumps(rec(i)) for i in range(900))
    return [text.encode(), js.encode(), js2.encode(), (text[:20000] + js[:20000]).encode()]

if __name__ == "__main__":
    docs = gen()
    total_in = total_out = 0
    t0 = time.time()
    for d in docs:
        c = squeeze.compress(d)
        if squeeze.decompress(c) != d:
            print(0); sys.exit(0)
        total_in += len(d); total_out += len(c)
    assert squeeze.decompress(squeeze.compress(b"")) == b""
    print("%.4f" % (total_in / total_out))
