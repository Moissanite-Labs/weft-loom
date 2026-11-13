"""Fitness for squeeze.py: compression ratio on a fixed, seeded mix of
English-like text and JSON. Prints one number (higher is better), 0 if any
round-trip fails."""
import json
import random
import sys

WORDS = (
    "the of and to a in is that it was for on are as with his they at be this "
    "from have or by one had not but what all were when we there can an your "
    "which their said if do will each about how up out them then she many some "
    "so these would other into has more her two like him see time could no make "
    "than first been its who now people my made over did down only way find use "
    "may water long little very after words called just where most know get "
    "through back much before go good new write our used me man too any day same "
    "right look think also around another came come work three word must because "
    "does part even place well such here take why things help put years different "
    "away again off went old number great tell men say small every found still "
    "between name should home big give air line set own under read last never us "
    "left end along while might next sound below saw something thought both few "
    "those always looked show large often together asked house world going want "
    "school important until form food keep children feet land side without boy "
    "once animals life enough took sometimes four head above kind began almost "
    "live page got earth need far hand high year mother light parts country "
    "father let night following picture being study second eyes soon times story "
    "boys since white days ever paper hard near sentence better best across "
    "during today others however sure means knew try told young miles sun ways "
    "thing whole hear example heard several change answer room sea against top "
    "turned learn point city play toward five using himself usually"
).split()

NAMES = ["alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi",
         "ivan", "judy", "mallory", "niaj", "olivia", "peggy", "rupert", "sybil"]
CITIES = ["London", "Paris", "Berlin", "Madrid", "Rome", "Vienna", "Prague",
          "Lisbon", "Dublin", "Oslo", "Helsinki", "Warsaw"]
TAGS = ["new", "sale", "vip", "trial", "beta", "internal", "archived", "flagged"]


def make_text(rng, n_bytes):
    # Zipf-ish word choice so it looks like English frequency statistics.
    weights = [1.0 / (i + 1) for i in range(len(WORDS))]
    out = []
    size = 0
    while size < n_bytes:
        para = []
        for _ in range(rng.randint(3, 7)):
            n = rng.randint(5, 18)
            ws = rng.choices(WORDS, weights=weights, k=n)
            s = " ".join(ws)
            if rng.random() < 0.3:
                k = rng.randint(1, n - 1)
                s = " ".join(ws[:k]) + ", " + " ".join(ws[k:])
            s = s[0].upper() + s[1:] + rng.choice([".", ".", ".", "?", "!"])
            para.append(s)
        p = " ".join(para) + "\n\n"
        out.append(p)
        size += len(p)
    return "".join(out).encode()


def make_json(rng, n_bytes):
    recs = []
    size = 0
    i = 0
    while size < n_bytes:
        i += 1
        rec = {
            "id": i,
            "uuid": "%032x" % rng.getrandbits(128),
            "name": rng.choice(NAMES),
            "email": "%s%d@example.com" % (rng.choice(NAMES), rng.randint(1, 999)),
            "city": rng.choice(CITIES),
            "age": rng.randint(18, 90),
            "balance": round(rng.uniform(0, 10000), 2),
            "active": rng.random() < 0.7,
            "tags": rng.sample(TAGS, rng.randint(0, 3)),
            "created": "20%02d-%02d-%02dT%02d:%02d:%02dZ" % (
                rng.randint(10, 24), rng.randint(1, 12), rng.randint(1, 28),
                rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)),
            "note": " ".join(rng.choices(WORDS, k=rng.randint(3, 10))),
        }
        s = json.dumps(rec)
        recs.append(s)
        size += len(s) + 2
    return ("[" + ",\n".join(recs) + "]").encode()


def corpus():
    rng = random.Random(20240607)
    text = make_text(rng, 300_000)
    js = make_json(rng, 300_000)
    return [text, js, text[:60_000] + js[:60_000], b"", b"x", bytes(range(256))]


def main():
    import squeeze
    items = corpus()
    raw = comp = 0
    for d in items:
        c = squeeze.compress(d)
        if not isinstance(c, bytes) or squeeze.decompress(c) != d:
            print(0)
            return
        # only the three real corpus items count toward the ratio
        if len(d) > 1000:
            raw += len(d)
            comp += len(c)
    print("%.4f" % (raw / comp))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # any failure scores 0
        sys.stderr.write("error: %r\n" % (e,))
        print(0)
