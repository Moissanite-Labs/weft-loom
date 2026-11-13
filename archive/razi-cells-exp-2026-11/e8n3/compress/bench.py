import json
import random
import time
import squeeze

def generate_data():
    rng = random.Random(42)
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
        "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
        "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
        "system", "data", "process", "information", "network", "application", "service",
        "user", "request", "response", "status", "error", "message", "timestamp", "value",
        "configuration", "performance", "optimization", "compression", "algorithm"
    ]
    
    # Generate English-like text paragraphs
    paragraphs = []
    for _ in range(300):
        sentences = []
        for _ in range(rng.randint(4, 10)):
            length = rng.randint(6, 20)
            sent_words = [rng.choice(words) for _ in range(length)]
            sent_words[0] = sent_words[0].capitalize()
            sentences.append(" ".join(sent_words) + ".")
        paragraphs.append(" ".join(sentences))
    english_text = "\n\n".join(paragraphs)
    
    # Generate JSON records
    records = []
    for i in range(1500):
        rec = {
            "id": i,
            "uuid": f"user-{rng.randint(1000, 9999)}-{rng.choice(words)}",
            "active": rng.choice([True, False]),
            "score": round(rng.uniform(0, 1000), 2),
            "tags": [rng.choice(words) for _ in range(rng.randint(1, 5))],
            "description": " ".join(rng.choice(words) for _ in range(rng.randint(5, 15))),
            "meta": {
                "created_at": f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z",
                "status": rng.choice(["ok", "pending", "failed", "retry"]),
                "retries": rng.randint(0, 5)
            }
        }
        records.append(rec)
    json_text = json.dumps({"version": "1.0", "count": len(records), "items": records}, indent=2)
    
    combined = (english_text + "\n---JSON_START---\n" + json_text).encode("utf-8")
    return combined, english_text.encode("utf-8"), json_text.encode("utf-8")

def main():
    combined, eng, jsn = generate_data()
    t0 = time.time()
    
    # Verify round-trip on edge cases and datasets
    for sample in [b"", b"a", b"hello world", bytes(range(256)), eng, jsn, combined]:
        comp = squeeze.compress(sample)
        if not isinstance(comp, (bytes, bytearray)):
            print(0)
            return
        decomp = squeeze.decompress(comp)
        if decomp != sample:
            print(0)
            return

    comp = squeeze.compress(combined)
    ratio = len(combined) / len(comp)
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
