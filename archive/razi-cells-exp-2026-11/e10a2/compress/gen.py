import random, json
WORDS = ("the of and to a in is that it was for on are as with his they at be this from have or by one had not but what all were when we there can an your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know get through back much before go good new write our used me man too any day same right look think also around another came come work three word must because does part even place well such here take why things help put years different away again off went old number great tell men say small every found still between name should home big give air line set own under read last never us left end along while might next sound below saw something thought both few those always looked show large often together asked house world going want school important until form food keep children feet land side without boy once animals life enough took sometimes four head above kind began almost live page got earth need far hand high year mother light parts country father let night following picture being study second eyes soon times story boys since white days ever paper hard near sentence better best across during today others however sure means knew try told young miles sun ways thing whole hear example heard several change answer room sea against top turned learn point city play toward five using himself usually").split()
def text(r, n):
    w = [1.0/(i+1) for i in range(len(WORDS))]
    out = []; size = 0
    while size < n:
        para = []
        for _ in range(r.randint(2, 7)):
            ws = r.choices(WORDS, w, k=r.randint(4, 18))
            s = " ".join(ws); s = s[0].upper() + s[1:]
            if r.random() < 0.3:
                i = s.find(" ", len(s)//2)
                if i > 0: s = s[:i] + "," + s[i:]
            para.append(s + r.choice([".", ".", ".", "?", "!"]))
        p = " ".join(para) + "\n\n"
        out.append(p); size += len(p)
    return "".join(out)
def js(r, n):
    names = ["alice","bob","carol","dave","erin","frank","grace","heidi","ivan","judy","mallory","niaj","olivia","peggy","rupert","sybil","trent","victor","walter"]
    tags = ["red","green","blue","urgent","low","archived","beta","internal","public","draft"]
    recs = []; size = 0; i = 0
    while size < n:
        i += 1
        nm = r.choice(names)
        rec = {"id": i, "uuid": "%032x" % r.getrandbits(128) if r.random() < 0.3 else None,
               "name": nm, "email": "%s%d@example.%s" % (nm, r.randint(1, 99), r.choice(["com","org","net"])),
               "active": r.random() < 0.7, "score": round(r.gauss(50, 15), 2),
               "tags": r.sample(tags, r.randint(0, 4)),
               "created": "20%02d-%02d-%02dT%02d:%02d:%02dZ" % (r.randint(10, 24), r.randint(1, 12), r.randint(1, 28), r.randint(0, 23), r.randint(0, 59), r.randint(0, 59)),
               "address": {"city": r.choice(WORDS[100:160]).title(), "zip": "%05d" % r.randint(0, 99999), "geo": [round(r.uniform(-90, 90), 4), round(r.uniform(-180, 180), 4)]},
               "note": " ".join(r.choices(WORDS, k=r.randint(0, 8)))}
        s = json.dumps(rec, indent=r.choice([None, None, 2]))
        recs.append(s); size += len(s) + 1
    return "\n".join(recs)
def corpus():
    r = random.Random(20240601)
    return [text(r, 150000).encode(), js(r, 150000).encode(), (text(r, 30000) + js(r, 30000)).encode(), b"", b"x", bytes(range(256))]
