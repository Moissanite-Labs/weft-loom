import random, json, sys, time
sys.path.insert(0, ".")
import squeeze

def gen():
    r = random.Random(12345)
    words = ("the of and to in a is that for it as was with be by on not he I this are or his from at which but have an they you were her she there been one all we can has would their what will if more when who so no said about up out them into than its time only could new other some these two may then do first any my now such like our over man me even most made after also did many before must through back years where much your way well down should because each just those people Mr how too little state good very make world still own see men work long get here between both life being under never day same another know while last might us great old year off come since against go came right used take three states himself few house use during without again place American around however home small found Mrs thought went say part once general high upon school every don't does got united left number course war until always away something fact though water less public put think almost hand enough far took head yet government system better set told nothing night end why called didn't eyes find going look asked later knew point next program city business give group toward young days let room president side social given present several order national second possible rather per face among form important often things looked early white case become large need big four within felt along children saw best church ever least power development light thing seemed family interest want members mind country area others turned although open god service certain kind problem began different door thus help means sense whole matter perhaps itself times human law line above name example action company hands local show whether five history gave today either act feet across taken anything quite having seen death week body experience really word words already themselves information college tell together shall held keep sure free real probably seems political question behind cannot office brought special major heard problems federal become".split())
    out = []
    # English-like text
    for _ in range(6000):
        n = r.randint(6, 18)
        s = " ".join(r.choice(words) for _ in range(n))
        out.append(s[0].upper() + s[1:] + r.choice([". ", ". ", "! ", "? ", ".\n"]))
    text = "".join(out).encode()
    # JSON records
    recs = []
    for i in range(4000):
        recs.append({"id": i, "name": r.choice(words) + " " + r.choice(words),
                     "email": r.choice(words) + str(r.randint(1, 999)) + "@example.com",
                     "active": r.random() < 0.7, "score": round(r.random() * 100, 3),
                     "tags": [r.choice(words) for _ in range(r.randint(0, 5))],
                     "address": {"city": r.choice(words).title(), "zip": "%05d" % r.randint(0, 99999),
                                 "lat": round(r.uniform(-90, 90), 5), "lon": round(r.uniform(-180, 180), 5)},
                     "created": "2023-%02d-%02dT%02d:%02d:%02dZ" % (r.randint(1, 12), r.randint(1, 28), r.randint(0, 23), r.randint(0, 59), r.randint(0, 59))})
    js = json.dumps(recs, indent=2).encode()
    js2 = "\n".join(json.dumps(x) for x in recs[:1500]).encode()
    return [text, js, js2]

def main():
    data = gen()
    total_in = total_out = 0
    for d in data:
        c = squeeze.compress(d)
        if squeeze.decompress(c) != d:
            print(0); return
        total_in += len(d); total_out += len(c)
    # edge cases
    for e in [b"", b"a", b"ab" * 3, bytes(range(256)) * 10]:
        if squeeze.decompress(squeeze.compress(e)) != e:
            print(0); return
    print("%.4f" % (total_in / total_out))

if __name__ == "__main__":
    main()
