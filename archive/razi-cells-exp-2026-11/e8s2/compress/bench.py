import json
import random
import pydoc
import inspect
import squeeze

def make_corpus():
    rng = random.Random(42)
    
    # Gather English-like prose from stdlib docstrings and modules
    modules = [json, random, pydoc, inspect]
    docs = []
    for m in modules:
        for name, obj in inspect.getmembers(m):
            doc = inspect.getdoc(obj)
            if doc and len(doc) > 40:
                docs.append(doc)
    
    words = "the of and to in a is that for it as was with be by on not he i this are or his from at which but have an had they you were their one all we can her has there been if more when will would who so no".split()
    words += "system data file process memory time user value function object string list number state error table record query network service request response config status message result index key type name".split()
    
    paragraphs = []
    for _ in range(400):
        if rng.random() < 0.4 and docs:
            paragraphs.append(rng.choice(docs))
        else:
            sents = []
            for _ in range(rng.randint(3, 8)):
                w = [rng.choice(words) for _ in range(rng.randint(8, 22))]
                w[0] = w[0].capitalize()
                sents.append(" ".join(w) + ".")
            paragraphs.append(" ".join(sents))
    english_text = "\n\n".join(paragraphs).encode("utf-8")
    
    # Generate realistic JSON records
    records = []
    for i in range(1200):
        rec = {
            "id": i,
            "uuid": f"usr-{rng.randint(10000, 99999)}-{i:04d}",
            "name": f"{rng.choice(words).capitalize()} {rng.choice(words).capitalize()}",
            "active": rng.choice([True, False, True]),
            "score": round(rng.uniform(0, 1000), 2),
            "tags": [rng.choice(words) for _ in range(rng.randint(1, 5))],
            "metadata": {
                "created_at": f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:00:00Z",
                "region": rng.choice(["us-east-1", "eu-west-1", "ap-south-1", "us-west-2"]),
                "retries": rng.randint(0, 5),
                "notes": rng.choice(docs)[:120] if docs else "standard entry",
            }
        }
        records.append(rec)
    json_text = json.dumps({"version": 1, "count": len(records), "items": records}, indent=2).encode("utf-8")
    
    # Interleaved mix as well
    mixed_chunks = []
    for i in range(200):
        mixed_chunks.append(paragraphs[i % len(paragraphs)].encode("utf-8"))
        mixed_chunks.append(json.dumps(records[i % len(records)]).encode("utf-8"))
    mixed_text = b"\n".join(mixed_chunks)
    
    return [english_text, json_text, mixed_text, english_text + b"\n" + json_text]

def main():
    corpora = make_corpus()
    # Edge cases for correctness check
    edge_cases = [
        b"",
        b"a",
        b"\x00" * 1000,
        bytes(range(256)) * 10,
        random.Random(99).randbytes(4096),
    ]
    for data in edge_cases:
        try:
            c = squeeze.compress(data)
            if not isinstance(c, (bytes, bytearray)) or squeeze.decompress(c) != data:
                print(0)
                return
        except Exception:
            print(0)
            return

    total_raw = 0
    total_comp = 0
    for data in corpora:
        try:
            c = squeeze.compress(data)
            if not isinstance(c, (bytes, bytearray)) or squeeze.decompress(c) != data:
                print(0)
                return
            total_raw += len(data)
            total_comp += len(c)
        except Exception:
            print(0)
            return

    ratio = total_raw / total_comp
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
