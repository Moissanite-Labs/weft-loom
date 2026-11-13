import json
import random
import time
import squeeze

def make_corpus():
    rng = random.Random(42)
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "system", "process", "data", "record", "value", "string", "number", "object",
        "compression", "algorithm", "entropy", "dictionary", "model", "context", "stream",
        "performance", "benchmark", "evaluation", "function", "parameter", "result", "error",
        "network", "request", "response", "header", "payload", "status", "timestamp", "user"
    ]
    # Build phrases and paragraphs of English-like text
    sentences = []
    for _ in range(120):
        length = rng.randint(6, 18)
        s = " ".join(rng.choices(words, k=length)).capitalize() + rng.choice([".", ".", ".", "!", "?"])
        sentences.append(s)

    paragraphs = []
    for _ in range(400):
        p = " ".join(rng.choices(sentences, k=rng.randint(3, 8)))
        paragraphs.append(p)
    english_text = "\n\n".join(paragraphs).encode("utf-8")

    # Build JSON records
    records = []
    for i in range(1500):
        rec = {
            "id": i,
            "uuid": f"usr-{rng.randint(1000, 9999)}-{i:04d}",
            "active": rng.choice([True, False, True]),
            "role": rng.choice(["admin", "editor", "viewer", "guest"]),
            "score": round(rng.uniform(0.0, 100.0), 2),
            "tags": rng.sample(words[:30], k=rng.randint(1, 5)),
            "message": rng.choice(sentences),
            "meta": {
                "retries": rng.randint(0, 5),
                "region": rng.choice(["us-east", "us-west", "eu-central", "ap-south"]),
                "status": rng.choice(["ok", "pending", "cached", "error"])
            }
        }
        records.append(rec)
    json_text = json.dumps({"version": "1.0", "count": len(records), "items": records}, indent=2).encode("utf-8")

    # Also test chunks: English only, JSON only, combined
    combined = english_text + b"\n" + json_text
    return [english_text, json_text, combined]

def main():
    corpora = make_corpus()
    # Edge cases check
    edge_cases = [
        b"",
        b"a",
        b"hello world" * 100,
        bytes(range(256)) * 4,
        random.Random(99).randbytes(2048),
    ]
    for ec in edge_cases:
        c = squeeze.compress(ec)
        if not isinstance(c, (bytes, bytearray)):
            print(0)
            return
        d = squeeze.decompress(c)
        if d != ec:
            print(0)
            return

    total_raw = 0
    total_comp = 0
    for data in corpora:
        c = squeeze.compress(data)
        if not isinstance(c, (bytes, bytearray)):
            print(0)
            return
        d = squeeze.decompress(c)
        if d != data:
            print(0)
            return
        total_raw += len(data)
        total_comp += len(c)

    ratio = total_raw / total_comp
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
