"""Deterministic corpus + scoring for squeeze.py. Prints ratio (>0), higher is better."""
import json
import random

WORDS = (
    "the of and to in a is that it was for on are as with his they at be this from have or by one had "
    "not but what all were when we there can an your which their said if do will each about how up out "
    "them then she many some so these would other into has more her two like him see time could no make "
    "than been its who now people my made over did down only way find use may water long little very after "
    "words called just where most know get through back much before go good new write our used me man too "
    "any day same right look think also around another came come work three word must because does part even "
    "place well such here take why help put different away again off went old number great tell men say small "
    "every found still between name should home big give air line set own under read last never us left end "
    "along while might next sound below saw something thought both few those always show large often together "
    "asked house don't world going want school important until form food keep children feet land side without "
    "boy once animal life enough took sometimes four head above kind began almost live page got earth need far "
    "hand high year mother light country father let night picture being study second soon story since white ever "
    "paper hard near sentence better best across during today however sure knew try told young sun thing whole "
    "hear example heard several change answer room sea against top turned learn point city play toward five himself"
).split()

PUNCT = [".", ",", ";", ":", "?", "!", " -", "..."]


def gen_text(rng, n_sentences):
    out = []
    for _ in range(n_sentences):
        n = rng.randint(6, 22)
        words = [rng.choice(WORDS) for _ in range(n)]
        words[0] = words[0].capitalize()
        s = " ".join(words)
        # occasional comma
        if n > 9 and rng.random() < 0.6:
            i = rng.randint(3, n - 3)
            parts = s.split(" ")
            parts[i] = parts[i] + ","
            s = " ".join(parts)
        s += rng.choice(PUNCT)
        out.append(s)
    # paragraphs
    text = ""
    for i, s in enumerate(out):
        text += s
        if (i + 1) % rng.randint(3, 7) == 0:
            text += "\n\n"
        else:
            text += " "
    return text


def gen_json(rng, n):
    kind = rng.random()
    if kind < 0.35:
        # array of records
        recs = []
        for _ in range(n):
            recs.append({
                "id": rng.randint(1, 10**6),
                "name": " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 3))),
                "active": rng.random() < 0.5,
                "score": round(rng.uniform(0, 100), 3),
                "tags": [rng.choice(WORDS) for _ in range(rng.randint(0, 4))],
                "meta": {"created": "20%02d-%02d-%02dT%02d:%02d:%02dZ" % (
                    rng.randint(10, 25), rng.randint(1, 12), rng.randint(1, 28),
                    rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)),
                    "nested": {"a": rng.randint(-100, 100), "b": [1, 2, 3][:rng.randint(0, 3)]}},
            })
        return json.dumps(recs, indent=2)
    if kind < 0.7:
        # config-like nested
        cfg = {"version": "1.%d.%d" % (rng.randint(0, 9), rng.randint(0, 20)),
               "services": {}}
        for _ in range(rng.randint(3, 8)):
            cfg["services"][rng.choice(WORDS)] = {
                "enabled": rng.random() < 0.7,
                "ports": [rng.randint(1, 65535) for _ in range(rng.randint(1, 3))],
                "host": "%s.example.%s" % (rng.choice(WORDS), rng.choice(["com", "org", "net", "io"])),
                "retries": rng.randint(0, 10),
                "timeout_ms": rng.choice([100, 250, 500, 1000, 2500, 5000]),
            }
        return json.dumps(cfg, indent=2, sort_keys=True)
    # compact JSON lines
    lines = []
    for _ in range(n):
        lines.append(json.dumps({"t": rng.randint(1, 2**31), "u": "/api/v%d/%s/%d" % (
            rng.randint(1, 3), rng.choice(WORDS), rng.randint(1, 9999)),
            "s": rng.randint(200, 599), "ms": round(rng.uniform(0, 500), 2),
            "msg": " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 6)))}))
    return "\n".join(lines)


def corpus():
    rng = random.Random(1234)
    chunks = []
    chunks.append(gen_text(rng, 900).encode())
    chunks.append(gen_json(rng, 260).encode())
    chunks.append(gen_text(rng, 500).encode())
    chunks.append(gen_json(rng, 160).encode())
    chunks.append(gen_text(rng, 300).encode())
    return chunks


if __name__ == "__main__":
    import sys
    import time
    import squeeze

    chunks = corpus()
    raw = sum(len(c) for c in chunks)
    t0 = time.time()
    total = 0
    for i, c in enumerate(chunks):
        comp = squeeze.compress(c)
        back = squeeze.decompress(comp)
        if back != c:
            print("ROUNDTRIP_FAIL chunk %d" % i)
            sys.exit(0)
        total += len(comp)
    dt = time.time() - t0
    if total == 0:
        print("ZERO")
        sys.exit(0)
    ratio = raw / total
    sys.stderr.write("raw=%d comp=%d time=%.2fs\n" % (raw, total, dt))
    print("%.6f" % ratio)
