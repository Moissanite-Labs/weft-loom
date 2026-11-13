import random, json

def make_corpus():
    rng = random.Random(42)
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "system", "data", "process", "memory", "network", "performance", "model",
        "function", "value", "object", "string", "number", "array", "boolean",
        "request", "response", "server", "client", "status", "message", "error",
        "time", "user", "account", "active", "created", "updated", "version",
        "configuration", "service", "cluster", "node", "transaction", "record"
    ]
    
    parts = []
    # 1. English-like paragraphs (~500 KB)
    for _ in range(800):
        sent_count = rng.randint(3, 8)
        sents = []
        for _ in range(sent_count):
            w_count = rng.randint(6, 20)
            s = [rng.choice(words) for _ in range(w_count)]
            s[0] = s[0].capitalize()
            sents.append(" ".join(s) + rng.choice([".", ".", ".", "!", "?"]))
        parts.append(" ".join(sents) + "\n\n")
        
    # 2. JSON records (~500 KB)
    records = []
    for i in range(2500):
        rec = {
            "id": i,
            "user_id": f"usr_{rng.randint(1000, 9999)}",
            "status": rng.choice(["active", "pending", "closed", "archived"]),
            "score": round(rng.uniform(0, 100), 2),
            "tags": rng.sample(words[:30], k=rng.randint(1, 5)),
            "metadata": {
                "version": rng.randint(1, 10),
                "region": rng.choice(["us-east", "us-west", "eu-central", "ap-south"]),
                "active": rng.choice([True, False]),
            },
            "summary": " ".join(rng.choice(words) for _ in range(rng.randint(5, 15)))
        }
        records.append(rec)
    parts.append(json.dumps({"records": records, "total": len(records)}, indent=2))
    
    # 3. JSON lines (~300 KB)
    for i in range(2000):
        row = {
            "ts": 1700000000 + i * rng.randint(1, 60),
            "level": rng.choice(["INFO", "WARN", "ERROR", "DEBUG"]),
            "service": rng.choice(["auth", "payment", "search", "storage", "gateway"]),
            "msg": " ".join(rng.choice(words) for _ in range(rng.randint(4, 12))),
            "latency_ms": rng.randint(1, 500)
        }
        parts.append(json.dumps(row) + "\n")
        
    data = "".join(parts).encode("utf-8")
    with open("corpus.bin", "wb") as f:
        f.write(data)
    print("Corpus bytes:", len(data))

if __name__ == "__main__":
    make_corpus()
