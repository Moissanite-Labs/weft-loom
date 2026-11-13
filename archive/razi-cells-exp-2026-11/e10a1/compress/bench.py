"""Fitness for squeeze.py: compression ratio on a fixed text+JSON corpus. Prints 0 on any round-trip failure."""
import random, json, sys, os

WORDS = ("the of and to in a is that it was for on are as with his they at be this from have or by one had not but "
         "what all were when we there can an your which their said if do will each about how up out them then she many "
         "some so these would other into has more her two like him see time could no make than first been its who now "
         "people my made over did down only way find use may water long little very after words called just where most "
         "know get through back much before go good new write our used me man too any day same right look think also "
         "around another came come work three word must because does part even place well such here take why things "
         "help put years different away again off went old number great tell men say small every found still between "
         "name should home big give air line set own under read last never us left end along while might next sound "
         "below saw something thought both few those always looked show large often together asked house world going "
         "want school important until form food keep children feet land side without boy once animals life enough took "
         "sometimes four head above kind began almost live page got earth need far hand high year mother light country "
         "father let night picture being study second soon story since white ever paper hard near sentence better best "
         "across during today however sure knew try told young sun thing whole hear example heard several change answer "
         "room sea against top turned learn point city play toward five himself usually money seen car morning").split()


def corpus():
    r = random.Random(20240607)
    # English-like text: Zipf-ish word choice, sentences, paragraphs
    weights = [1.0 / (i + 1) ** 0.9 for i in range(len(WORDS))]
    paras = []
    while sum(map(len, paras)) < 300_000:
        sents = []
        for _ in range(r.randint(2, 7)):
            n = r.randint(4, 18)
            ws = r.choices(WORDS, weights, k=n)
            if r.random() < 0.3:
                ws.insert(r.randrange(1, n), str(r.randint(1, 9999)))
            s = " ".join(ws)
            if r.random() < 0.35:
                k = r.randrange(2, n - 1)
                parts = s.split(" ")
                parts[k] += ","
                s = " ".join(parts)
            sents.append(s[0].upper() + s[1:] + r.choice(".....?!"))
        paras.append(" ".join(sents))
    text = "\n\n".join(paras).encode()
    # JSON: records with mixed field types
    recs = []
    for i in range(1800):
        recs.append({
            "id": i,
            "uuid": "%032x" % r.getrandbits(128),
            "name": " ".join(r.choices(WORDS, k=2)).title(),
            "email": "%s.%s@example.%s" % (r.choice(WORDS), r.choice(WORDS), r.choice(["com", "org", "net"])),
            "active": r.random() < 0.7,
            "score": round(r.uniform(0, 100), 3),
            "tags": r.sample(WORDS[40:120], r.randint(0, 4)),
            "geo": {"lat": round(r.uniform(-90, 90), 5), "lon": round(r.uniform(-180, 180), 5)},
            "created": "20%02d-%02d-%02dT%02d:%02d:%02dZ" % (r.randint(10, 24), r.randint(1, 12), r.randint(1, 28),
                                                             r.randint(0, 23), r.randint(0, 59), r.randint(0, 59)),
            "note": " ".join(r.choices(WORDS, weights, k=r.randint(3, 12))) if r.random() < 0.6 else None,
        })
    js = json.dumps(recs, indent=1).encode()
    return [text, js, text[:50_000] + js[:50_000]]


def main():
    try:
        import squeeze
        parts = corpus()
        r = random.Random(1)
        edge = [b"", b"a", b"\x00" * 1000, bytes(r.getrandbits(8) for _ in range(3000)), bytes(range(256)) * 3,
                "héllo wörld ✓ ".encode() * 50]
        for e in edge:
            if squeeze.decompress(squeeze.compress(e)) != e:
                print(0); return
        raw = comp = 0
        for p in parts:
            c = squeeze.compress(p)
            if squeeze.decompress(c) != p:
                print(0); return
            raw += len(p); comp += len(c)
        if "-v" in sys.argv:
            print([len(p) for p in parts], raw, comp, file=sys.stderr)
        print("%.4f" % (raw / comp))
    except Exception as ex:
        if "-v" in sys.argv:
            raise
        print(0)


if __name__ == "__main__":
    main()
