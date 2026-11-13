import json
import random
import time
import squeeze

def generate_corpus():
    rng = random.Random(424242)
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
        "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
        "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
        "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
        "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
        "system", "data", "process", "information", "service", "application", "network",
        "user", "configuration", "performance", "request", "response", "status", "error",
        "message", "timestamp", "identifier", "transaction", "account", "balance", "active",
        "pending", "completed", "failed", "organization", "department", "engineering",
        "research", "development", "production", "environment", "cluster", "node", "region"
    ]
    # Add some morphological variants
    extra = []
    for w in words[40:]:
        extra.extend([w + "s", w + "ed", w + "ing", w + "ly"])
    all_words = words * 5 + extra

    chunks = []
    # 1. English-like paragraphs
    for _ in range(400):
        sents = []
        for _ in range(rng.randint(4, 10)):
            length = rng.randint(6, 22)
            sent_words = [rng.choice(all_words) for _ in range(length)]
            sent_words[0] = sent_words[0].capitalize()
            if rng.random() < 0.25 and length > 8:
                sent_words[length // 2] += ","
            sents.append(" ".join(sent_words) + rng.choice([".", ".", ".", "!", "?"]))
        chunks.append(" ".join(sents) + "\n\n")

    # 2. JSON records (API logs, user profiles, nested configs)
    records = []
    regions = ["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1"]
    statuses = ["active", "pending", "completed", "failed", "archived"]
    for i in range(1200):
        rec = {
            "id": i + 100000,
            "uuid": f"usr-{rng.randint(1000,9999)}-{rng.randint(100000,999999)}",
            "timestamp": f"2025-0{rng.randint(1,9)}-{rng.randint(10,28)}T{rng.randint(10,23)}:{rng.randint(10,59)}:{rng.randint(10,59)}Z",
            "status": rng.choice(statuses),
            "region": rng.choice(regions),
            "score": round(rng.uniform(0.0, 1000.0), 3),
            "active": rng.choice([True, False]),
            "tags": rng.sample(words[100:], k=rng.randint(2, 6)),
            "description": " ".join(rng.choice(all_words) for _ in range(rng.randint(8, 20))) + ".",
            "metrics": {
                "latency_ms": rng.randint(1, 500),
                "retries": rng.randint(0, 5),
                "bytes_sent": rng.randint(128, 65536),
            }
        }
        records.append(rec)
    chunks.append(json.dumps({"records": records, "version": "1.0.4", "count": len(records)}, indent=2) + "\n")

    # 3. JSON lines mixed with text logs
    for i in range(800):
        line_obj = {
            "seq": i,
            "level": rng.choice(["INFO", "WARN", "ERROR", "DEBUG"]),
            "msg": " ".join(rng.choice(all_words) for _ in range(rng.randint(5, 15))),
            "code": rng.choice([200, 200, 200, 201, 400, 404, 500]),
        }
        chunks.append(json.dumps(line_obj) + "\n")

    # Also test edge cases inside corpus or separate verification
    return "".join(chunks).encode("utf-8")

def verify_edge_cases():
    cases = [
        b"",
        b"a",
        b"\x00\xff\x00\xff" * 100,
        b'{"a": 1, "b": [true, false, null, "hello world"]}\n' * 50,
        bytes(range(256)) * 10,
    ]
    for c in cases:
        comp = squeeze.compress(c)
        if not isinstance(comp, (bytes, bytearray)):
            return False
        decomp = squeeze.decompress(bytes(comp))
        if decomp != c:
            return False
    return True

if __name__ == "__main__":
    if not verify_edge_cases():
        print(0)
        raise SystemExit(0)
    data = generate_corpus()
    comp = squeeze.compress(data)
    if not isinstance(comp, (bytes, bytearray)) or len(comp) == 0:
        print(0)
        raise SystemExit(0)
    decomp = squeeze.decompress(bytes(comp))
    if decomp != data:
        print(0)
        raise SystemExit(0)
    ratio = len(data) / len(comp)
    print(f"{ratio:.6f}")
