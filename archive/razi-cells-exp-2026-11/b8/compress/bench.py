import random
import json
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
        "system", "data", "process", "memory", "function", "network", "protocol",
        "configuration", "performance", "optimization", "compression", "algorithm",
        "structure", "analysis", "application", "development", "environment",
        "interface", "management", "operation", "parameter", "reconstruct",
        "representation", "specification", "transformation", "verification"
    ]
    
    parts = []
    # 1. English-like paragraphs with Markov-like bias and punctuation
    for _ in range(400):
        sent_len = rng.randint(8, 25)
        sent = [rng.choice(words[:30] if rng.random() < 0.65 else words) for _ in range(sent_len)]
        sent[0] = sent[0].capitalize()
        paragraph = " ".join(sent) + rng.choice([". ", ". ", "! ", "? ", ".\n"])
        parts.append(paragraph)
    
    # 2. Structured JSON records
    records = []
    for i in range(600):
        rec = {
            "id": i,
            "uuid": f"user-{i:05d}-{rng.randint(1000, 9999)}",
            "active": rng.choice([True, False, True]),
            "role": rng.choice(["admin", "editor", "viewer", "guest"]),
            "score": round(rng.uniform(0, 100), 2),
            "tags": rng.sample(words[50:], k=rng.randint(1, 5)),
            "description": " ".join(rng.choice(words) for _ in range(rng.randint(5, 18))),
            "meta": {
                "created_at": f"2025-0{rng.randint(1,9)}-{rng.randint(10,28)}T12:00:00Z",
                "retries": rng.randint(0, 5),
                "region": rng.choice(["us-east-1", "eu-west-1", "ap-south-1"])
            }
        }
        records.append(rec)
    parts.append(json.dumps({"users": records, "version": "1.0.4", "status": "ok"}, indent=2))
    
    # Repeat with slight variations to get ~400KB workload
    full_text = "\n".join(parts)
    data = (full_text + "\n" + full_text[::-1][:20000]).encode("utf-8")
    return data

def main():
    raw = make_corpus()
    t0 = time.perf_counter()
    comp = squeeze.compress(raw)
    if not isinstance(comp, (bytes, bytearray)):
        print(0)
        return
    comp = bytes(comp)
    decomp = squeeze.decompress(comp)
    dt = time.perf_counter() - t0
    if decomp != raw or len(comp) == 0:
        print(0)
        return
    # Also test edge cases
    for edge in [b"", b"a", b"aaaa", b"\x00\xff\x00\xff" * 100, bytes(range(256))]:
        if squeeze.decompress(squeeze.compress(edge)) != edge:
            print(0)
            return
    ratio = len(raw) / len(comp)
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
