"""Generate a fixed mix of English-like text + JSON and benchmark compressors."""
import json, random, time, lzma, bz2, zlib, sys

WORDS = ("the of and to in a is that it was for on are as with his they at be this from have or by one had not but what all were when we there can an "
         "your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could "
         "no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know "
         "system data value string number object array true false null error request response server client handler config default index result message status "
         "user name email address phone country city street postal code item list price quantity total amount currency payment method order product customer").split()

def gen_text(rng, nchars):
    out = []
    n = 0
    sent_start = True
    while n < nchars:
        r = rng.random()
        w = rng.choice(WORDS)
        if sent_start:
            w = w.capitalize()
            sent_start = False
        out.append(w)
        n += len(w) + 1
        if r < 0.06:
            out[-1] += rng.choice([",", ";", ".", ".", "?"])
            if out[-1].endswith((".", "?", "!")):
                sent_start = True
        if r > 0.985:
            out[-1] += "\n\n"
        elif r > 0.90:
            out[-1] += "\n"
    return " ".join(out)

def gen_json_compact(rng, n):
    recs = []
    for i in range(n):
        recs.append({
            "id": 100000 + i,
            "name": rng.choice(WORDS).capitalize() + " " + rng.choice(WORDS).capitalize(),
            "email": rng.choice(WORDS) + "." + rng.choice(WORDS) + str(rng.randint(1, 99)) + "@example.com",
            "ts": "2024-%02d-%02dT%02d:%02d:%02dZ" % (rng.randint(1,12), rng.randint(1,28), rng.randint(0,23), rng.randint(0,59), rng.randint(0,59)),
            "status": rng.choice(["active", "inactive", "pending", "error"]),
            "score": round(rng.uniform(0, 100), 3),
            "tags": [rng.choice(WORDS) for _ in range(rng.randint(1, 3))],
        })
    return json.dumps(recs, separators=(",", ":"))

def gen_json_pretty(rng, n):
    recs = []
    for i in range(n):
        recs.append({
            "identifier": i,
            "title": " ".join(rng.choice(WORDS) for _ in range(rng.randint(2, 6))),
            "meta": {"created": "2024-05-%02d" % rng.randint(1,28), "version": rng.randint(1, 9)},
            "enabled": rng.random() < 0.5,
            "values": [round(rng.gauss(0, 1), 4) for _ in range(4)],
        })
    return json.dumps(recs, indent=2)

def dataset():
    rng = random.Random(1234)
    parts = [
        gen_text(rng, 60000).encode(),
        gen_json_compact(rng, 350).encode(),
        gen_text(rng, 60000).encode(),
        gen_json_pretty(rng, 200).encode(),
        gen_text(rng, 40000).encode(),
        gen_json_compact(rng, 200).encode(),
    ]
    return b"\n".join(parts)

if __name__ == "__main__":
    d = dataset()
    print("data size", len(d))
    cfgs = []
    for lc in (0, 1, 2, 3, 4):
        for lp in (0, 1, 2):
            if lc + lp > 4:
                continue
            for pb in (0, 1, 2):
                cfgs.append((lc, lp, pb))
    base = dict(id=lzma.FILTER_LZMA1, dict_size=1 << 24, mode=lzma.MODE_NORMAL,
                nice_len=273, mf=lzma.MF_BT4, depth=0)
    res = []
    t0 = time.time()
    for (lc, lp, pb) in cfgs:
        f = dict(base); f.update(lc=lc, lp=lp, pb=pb)
        c = lzma.compress(d, format=lzma.FORMAT_RAW, filters=[f])
        res.append((len(c), lc, lp, pb))
    t1 = time.time()
    res.sort()
    for r in res[:8]:
        print("lzma lc=%d lp=%d pb=%d -> %d (%.4f)" % (r[1], r[2], r[3], r[0], r[0]/len(d)))
    print("all cfgs time %.2fs" % (t1-t0), "n=", len(cfgs))
    print("bz2", len(bz2.compress(d, 9)))
    print("zlib", len(zlib.compress(d, 9)))
