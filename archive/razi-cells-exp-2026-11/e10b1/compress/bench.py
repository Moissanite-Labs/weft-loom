"""Fitness for squeeze.py: compression ratio on a fixed, seeded corpus.

Corpus = English-like text (Zipf-distributed pseudo-word vocabulary, sentences,
paragraphs) + JSON records (ids, names, floats, timestamps, nested lists).
Prints total_raw / total_compressed, or 0 if any round-trip fails.
"""
import json
import random
import sys


def make_vocab(rng, n=3000):
    onsets = ["", "b", "c", "d", "f", "g", "h", "l", "m", "n", "p", "r", "s", "t", "w",
              "st", "tr", "ch", "sh", "th", "pl", "br", "gr", "cl", "pr"]
    nuclei = ["a", "e", "i", "o", "u", "ea", "ou", "ai", "oo", "ie"]
    codas = ["", "", "n", "r", "s", "t", "l", "d", "m", "ng", "st", "nt", "ck", "ll"]
    common = ["the", "of", "and", "to", "a", "in", "is", "that", "it", "was", "for", "on",
              "with", "as", "be", "at", "by", "this", "had", "not", "are", "but", "from",
              "or", "have", "an", "they", "which", "one", "you", "were", "her", "all",
              "she", "there", "would", "their", "we", "him", "been", "has", "when", "who",
              "will", "more", "no", "if", "out", "so", "said", "what", "up", "its", "about",
              "into", "than", "them", "can", "only", "other", "new", "some", "could", "time"]
    vocab = list(common)
    seen = set(vocab)
    while len(vocab) < n:
        syl = rng.choice([1, 2, 2, 3, 3, 4])
        w = "".join(rng.choice(onsets) + rng.choice(nuclei) + rng.choice(codas) for _ in range(syl))
        if w not in seen and len(w) > 1:
            seen.add(w)
            vocab.append(w)
    return vocab


def make_text(rng, target):
    vocab = make_vocab(rng)
    weights = [1.0 / (i + 1) ** 1.0 for i in range(len(vocab))]
    out = []
    size = 0
    while size < target:
        para = []
        for _ in range(rng.randint(3, 8)):
            n = rng.randint(5, 24)
            words = rng.choices(vocab, weights, k=n)
            parts = []
            for i, w in enumerate(words):
                if i == 0:
                    w = w.capitalize()
                elif rng.random() < 0.03:
                    w = w.capitalize()
                parts.append(w)
                if i < n - 1 and rng.random() < 0.08:
                    parts[-1] += rng.choice([",", ",", ",", ";", ":"])
            if rng.random() < 0.05:
                parts.append(str(rng.randint(1, 2025)))
            para.append(" ".join(parts) + rng.choice([".", ".", ".", ".", "?", "!"]))
        p = " ".join(para) + "\n\n"
        out.append(p)
        size += len(p)
    return "".join(out).encode("utf-8")


def make_json(rng, target):
    first = ["Ada", "Ben", "Cara", "Dev", "Elif", "Finn", "Gia", "Hugo", "Ines", "Jun",
             "Kai", "Lena", "Milo", "Nora", "Omar", "Pia", "Quinn", "Ravi", "Sara", "Tomas"]
    last = ["Abbott", "Baker", "Chen", "Diaz", "Evans", "Fischer", "Garcia", "Hughes",
            "Ito", "Jensen", "Khan", "Lopez", "Meyer", "Novak", "Okafor", "Patel"]
    tags = ["alpha", "beta", "urgent", "billing", "mobile", "web", "internal", "eu",
            "us", "trial", "legacy", "vip", "bot", "retry", "beta-2"]
    status = ["active", "pending", "suspended", "closed"]
    hexd = "0123456789abcdef"
    recs = []
    size = 0
    i = 0
    while size < target:
        i += 1
        fn, ln = rng.choice(first), rng.choice(last)
        rec = {
            "id": 100000 + i * rng.randint(1, 3),
            "uuid": "".join(rng.choice(hexd) for _ in range(32)),
            "name": fn + " " + ln,
            "email": "%s.%s%d@example.%s" % (fn.lower(), ln.lower(), rng.randint(1, 99),
                                             rng.choice(["com", "org", "net"])),
            "status": rng.choice(status),
            "score": round(rng.uniform(0, 100), 3),
            "balance": round(rng.gauss(1500, 900), 2),
            "created": "20%02d-%02d-%02dT%02d:%02d:%02dZ" % (
                rng.randint(15, 25), rng.randint(1, 12), rng.randint(1, 28),
                rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)),
            "verified": rng.random() < 0.7,
            "tags": rng.sample(tags, rng.randint(0, 4)),
            "geo": {"lat": round(rng.uniform(-90, 90), 5), "lon": round(rng.uniform(-180, 180), 5)},
            "notes": None if rng.random() < 0.5 else "ticket %d reopened %d times" % (
                rng.randint(1000, 99999), rng.randint(1, 9)),
        }
        s = json.dumps(rec)
        recs.append(s)
        size += len(s) + 2
    return ("[" + ",\n".join(recs) + "]").encode("utf-8")


def corpus():
    rng = random.Random(20240607)
    text = make_text(rng, 400_000)
    js = make_json(rng, 400_000)
    half_t, half_j = text[:100_000], js[:100_000]
    return [("text", text), ("json", js), ("mixed", half_t + half_j)]


def main():
    try:
        import squeeze
        raw = comp = 0
        detail = []
        for name, data in corpus():
            c = squeeze.compress(data)
            if not isinstance(c, (bytes, bytearray)):
                print(0); return
            d = squeeze.decompress(bytes(c))
            if d != data:
                print(0); return
            raw += len(data)
            comp += len(c)
            detail.append("%s %d->%d (%.3f)" % (name, len(data), len(c), len(data) / len(c)))
        # edge cases must round-trip too
        for edge in (b"", b"a", bytes(range(256)) * 3, b"\x00" * 5000):
            if squeeze.decompress(squeeze.compress(edge)) != edge:
                print(0); return
        if "-v" in sys.argv:
            print("\n".join(detail), file=sys.stderr)
        print("%.4f" % (raw / comp))
    except Exception as e:
        if "-v" in sys.argv:
            print("ERR", repr(e), file=sys.stderr)
        print(0)


if __name__ == "__main__":
    main()
