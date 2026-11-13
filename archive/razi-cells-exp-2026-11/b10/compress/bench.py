import json
import random
import time
import squeeze

def make_corpus():
    rng = random.Random(424242)
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "system", "data", "process", "memory", "network", "computation", "function",
        "variable", "object", "string", "number", "boolean", "array", "dictionary",
        "algorithm", "performance", "optimization", "compression", "entropy", "model",
        "structure", "analysis", "experimental", "observation", "measurement", "result",
        "temperature", "pressure", "velocity", "acceleration", "frequency", "wavelength",
        " running", " testing", " building", " creating", " updating", " deleting",
        "however", "therefore", "consequently", "furthermore", "nevertheless", "meanwhile"
    ]
    
    # 1. English-like text blocks (paragraphs, sentences, punctuation)
    text_parts = []
    for _ in range(800):
        sent_len = rng.randint(8, 25)
        sent = [rng.choice(words).strip() for _ in range(sent_len)]
        sent[0] = sent[0].capitalize()
        if rng.random() < 0.3:
             comma_pos = rng.randint(2, len(sent) - 2)
             sent[comma_pos] += ","
        text_parts.append(" ".join(sent) + rng.choice([". ", ". ", ". ", "! ", "? ", ".\n"]))
    english_text = "".join(text_parts).encode("utf-8")

    # 2. Structured JSON records (API responses, logs, nested objects)
    records = []
    statuses = ["active", "pending", "closed", "archived", "error"]
    roles = ["admin", "user", "guest", "moderator", "developer"]
    tags_pool = ["urgent", "backend", "frontend", "database", "security", "ui", "api", "v1", "v2"]
    for i in range(1200):
        rec = {
            "id": 100000 + i,
            "uuid": f"usr-{rng.randint(1000,9999)}-{i:04d}",
            "name": f"{rng.choice(words).strip().capitalize()} {rng.choice(words).strip().capitalize()}",
            "status": rng.choice(statuses),
            "role": rng.choice(roles),
            "score": round(rng.uniform(0, 1000), 2),
            "active": rng.choice([True, False]),
            "tags": rng.sample(tags_pool, k=rng.randint(1, 4)),
            "metrics": {
                "latency_ms": rng.randint(1, 500),
                "retries": rng.randint(0, 5),
                "region": rng.choice(["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1"]),
            },
            "notes": " ".join(rng.choice(words).strip() for _ in range(rng.randint(5, 15))) + "."
        }
        records.append(rec)
    json_bytes = json.dumps({"version": "2.4.0", "count": len(records), "items": records}, indent=2).encode("utf-8")

    # 3. JSON lines (log-style mix of JSON and English messages)
    jsonl_parts = []
    for i in range(1000):
        entry = {
            "ts": 1700000000 + i * rng.randint(1, 10),
            "level": rng.choice(["INFO", "INFO", "INFO", "WARN", "ERROR", "DEBUG"]),
            "service": rng.choice(["auth", "payment", "search", "storage", "gateway"]),
            "msg": " ".join(rng.choice(words).strip() for _ in range(rng.randint(6, 18))),
            "code": rng.choice([200, 200, 200, 201, 400, 404, 500]),
        }
        jsonl_parts.append(json.dumps(entry))
    jsonl_bytes = ("\n".join(jsonl_parts) + "\n").encode("utf-8")

    # Combine all into one payload, plus test chunks individually
    combined = english_text + b"\n---SPLIT---\n" + json_bytes + b"\n---SPLIT---\n" + jsonl_bytes
    return [english_text, json_bytes, jsonl_bytes, combined]

def main():
    samples = make_corpus()
    # Edge cases for correctness
    edge_cases = [
        b"",
        b"a",
        b"\x00\xff\x00\xff" * 100,
        bytes(range(256)) * 4,
        b'{"a": 1, "b": [true, false, null, "hello\\nworld"]}',
    ]
    for ec in edge_cases:
        c = squeeze.compress(ec)
        if not isinstance(c, (bytes, bytearray)):
            print(0)
            return
        d = squeeze.decompress(bytes(c))
        if d != ec:
            print(0)
            return

    total_raw = 0
    total_comp = 0
    for s in samples:
        c = squeeze.compress(s)
        if not isinstance(c, (bytes, bytearray)):
            print(0)
            return
        d = squeeze.decompress(bytes(c))
        if d != s:
            print(0)
            return
        total_raw += len(s)
        total_comp += len(c)

    ratio = total_raw / max(1, total_comp)
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
