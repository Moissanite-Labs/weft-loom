import json, random

WORDS = (
    "the be to of and a in that have I it for not on with he as you do at this but his by from they we say her she or an will my one all would there their what so up out if about who get which go me when make can like time no just him know take people into year your good some could them see other than then now look only come its over think also back after use two how our work first well way even new want because any these give day most us is are was were been has had did does doing"
).split()

SCHEMA_KEYS = ["id", "name", "email", "active", "score", "tags", "address", "city", "country", "created_at", "updated_at", "balance", "currency", "notes", "items", "meta"]


def english_like(nbytes, seed):
    r = random.Random(seed)
    out = []
    size = 0
    while size < nbytes:
        n = r.randint(5, 18)
        words = [r.choice(WORDS) for _ in range(n)]
        # Capitalize first word and end sentence; occasional punctuation.
        words[0] = words[0].capitalize()
        s = " ".join(words).rstrip(",.;:")
        end = r.choice([".", ".", ".", "!", "?"])
        if r.random() < 0.18 and n > 6:
            s = s[:-1] + "," + s[-1:]
        s += end + (" " if r.random() < 0.9 else "\n")
        out.append(s)
        size += len(s)
    return "".join(out).encode()[:nbytes]


def json_like(nbytes, seed):
    r = random.Random(seed + 100000)
    records = []
    size = 0
    i = 0
    while size < nbytes:
        i += 1
        first = r.choice(WORDS).capitalize()
        last = r.choice(WORDS).capitalize()
        rec = {
            "id": i,
            "name": first + " " + last,
            "email": (first + "." + last + str(i) + "@example.com").lower(),
            "active": r.random() < 0.75,
            "score": round(r.uniform(0, 100), 2),
            "tags": [r.choice(WORDS), r.choice(WORDS), r.choice(WORDS)],
            "address": str(r.randint(1, 9999)) + " " + r.choice(WORDS).capitalize() + " Street",
            "city": r.choice(["Springfield", "Riverside", "Franklin", "Greenville", "Bristol", "Clinton", "Fairview", "Salem"]),
            "country": r.choice(["US", "CA", "GB", "DE", "FR", "JP", "AU", "NL"]),
            "created_at": "2024-%02d-%02dT%02d:%02d:%02dZ" % (r.randint(1,12), r.randint(1,28), r.randint(0,23), r.randint(0,59), r.randint(0,59)),
            "balance": round(r.uniform(-1000, 10000), 2),
            "currency": r.choice(["USD", "EUR", "GBP", "JPY", "CAD"]),
            "notes": " ".join(r.choice(WORDS) for _ in range(r.randint(3, 12))),
            "items": [
                {"sku": "SKU-%05d" % r.randint(1, 99999), "qty": r.randint(1, 20), "price": round(r.uniform(1, 500), 2)}
                for _ in range(r.randint(0, 3))
            ],
            "meta": {"source": r.choice(["web", "api", "import", "mobile"]), "version": r.randint(1, 5)},
        }
        records.append(rec)
        size += len(json.dumps(rec, separators=(",", ":"))) + 2
    # Mix compact and indented JSON for a realistic fixed corpus.
    compact = json.dumps(records, separators=(",", ":")).encode()
    pretty = json.dumps(records[: max(1, len(records)//3)], indent=2, sort_keys=True).encode()
    blob = compact + b"\n" + pretty
    return blob[:nbytes]


def make_data():
    parts = [
        english_like(60000, 1),
        json_like(50000, 2),
        english_like(25000, 3),
        json_like(25000, 4),
    ]
    return b"\n\n".join(parts)


if __name__ == "__main__":
    data = make_data()
    print(len(data))
    with open("corpus.bin", "wb") as f:
        f.write(data)
