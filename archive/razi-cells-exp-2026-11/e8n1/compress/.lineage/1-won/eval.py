import json
import random
import time
import squeeze

def make_corpus():
    rng = random.Random(42)
    words = [
        "the", "of", "and", "to", "in", "a", "is", "that", "for", "it", "as", "was", "with", "be", "by", "on",
        "not", "he", "I", "this", "are", "or", "his", "from", "at", "which", "but", "have", "an", "had", "they",
        "you", "were", "their", "one", "all", "we", "can", "her", "has", "there", "been", "if", "more", "when",
        "will", "would", "who", "so", "no", "system", "data", "process", "information", "time", "user", "network",
        "service", "application", "server", "file", "memory", "value", "state", "performance", "function", "model",
        "configuration", "request", "response", "status", "error", "message", "version", "client", "result", "list",
        "object", "number", "string", "true", "false", "null", "compression", "algorithm", "dictionary", "entropy"
    ]
    # Zipfian weights
    weights = [1.0 / ((i + 1) ** 0.85) for i in range(len(words))]
    
    paragraphs = []
    for _ in range(400):
        sentences = []
        for _ in range(rng.randint(3, 8)):
            s_words = rng.choices(words, weights=weights, k=rng.randint(6, 20))
            s_words[0] = s_words[0].capitalize()
            sentences.append(" ".join(s_words) + rng.choice([".", ".", ".", "!", "?"]))
        paragraphs.append(" ".join(sentences))
    english_text = "\n\n".join(paragraphs)

    records = []
    for i in range(1500):
        rec = {
            "id": i,
            "uuid": f"user-{rng.randint(1000, 9999)}-{i:04d}",
            "active": rng.choice([True, False, True]),
            "role": rng.choice(["admin", "user", "viewer", "editor", "guest"]),
            "score": round(rng.uniform(0, 1000), 2),
            "tags": rng.sample(words[:30], k=rng.randint(1, 5)),
            "metadata": {
                "created_at": f"2025-0{rng.randint(1,9)}-{rng.randint(10,28)}T12:{rng.randint(10,59)}:00Z",
                "retries": rng.randint(0, 5),
                "region": rng.choice(["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1"]),
                "notes": " ".join(rng.choices(words, weights=weights, k=rng.randint(4, 12)))
            }
        }
        records.append(rec)
    json_text = json.dumps({"version": "1.0.0", "count": len(records), "items": records}, indent=2)

    combined = (english_text + "\n---JSON_SECTION---\n" + json_text).encode("utf-8")
    return combined

def main():
    data = make_corpus()
    # Also test edge cases
    edge_cases = [b"", b"a", b"hello world" * 100, bytes(range(256)) * 10, data]
    for case in edge_cases[:-1]:
        c = squeeze.compress(case)
        if not isinstance(c, bytes):
            print(0)
            return
        d = squeeze.decompress(c)
        if d != case:
            print(0)
            return

    comp = squeeze.compress(data)
    if not isinstance(comp, bytes):
        print(0)
        return
    decomp = squeeze.decompress(comp)
    if decomp != data:
        print(0)
        return

    ratio = len(data) / max(1, len(comp))
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
