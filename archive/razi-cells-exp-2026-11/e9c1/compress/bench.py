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
        "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
        "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
        "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
        "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
        "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
        "system", "data", "process", "function", "value", "string", "number", "object",
        "array", "result", "error", "message", "status", "request", "response", "server",
        "client", "user", "account", "created", "updated", "active", "configuration"
    ]
    
    # Generate English-like paragraphs
    paragraphs = []
    for _ in range(300):
        sentences = []
        for _ in range(rng.randint(4, 10)):
            length = rng.randint(6, 22)
            sent_words = [rng.choice(words) for _ in range(length)]
            sent_words[0] = sent_words[0].capitalize()
            if rng.random() < 0.3:
                idx = rng.randint(2, length - 2)
                sent_words[idx] += ","
            sentences.append(" ".join(sent_words) + ".")
        paragraphs.append(" ".join(sentences))
    english_text = "\n\n".join(paragraphs)

    # Generate JSON records
    records = []
    statuses = ["active", "pending", "suspended", "archived"]
    roles = ["admin", "editor", "viewer", "billing", "support"]
    for i in range(600):
        rec = {
            "id": 100000 + i,
            "uuid": f"usr-{100000+i:06d}-{rng.randint(1000,9999)}",
            "name": f"{rng.choice(words).capitalize()} {rng.choice(words).capitalize()}",
            "email": f"{rng.choice(words)}.{rng.choice(words)}{i}@example.org",
            "status": rng.choice(statuses),
            "roles": rng.sample(roles, k=rng.randint(1, 3)),
            "score": round(rng.uniform(0.0, 100.0), 2),
            "active": rng.choice([True, False]),
            "metadata": {
                "created_at": f"2025-0{rng.randint(1,9)}-{rng.randint(10,28)}T{rng.randint(10,23)}:{rng.randint(10,59)}:00Z",
                "login_count": rng.randint(0, 500),
                "notes": " ".join(rng.choice(words) for _ in range(rng.randint(5, 18))),
                "tags": [rng.choice(words) for _ in range(rng.randint(1, 4))]
            }
        }
        records.append(rec)
    json_text = json.dumps({"version": "1.0", "count": len(records), "users": records}, indent=2)

    # Interleave and combine
    combined = (english_text + "\n\n--- JSON DATA ---\n\n" + json_text).encode("utf-8")
    return combined

def verify_edge_cases():
    cases = [
        b"",
        b"a",
        b"hello world",
        b"\x00\xff\x00\xfe" * 100,
        bytes(range(256)) * 4,
        b'{"a": 1, "b": [true, false, null, "xyz"]}',
    ]
    for c in cases:
        comp = squeeze.compress(c)
        if not isinstance(comp, (bytes, bytearray)):
            return False
        decomp = squeeze.decompress(comp)
        if decomp != c:
            return False
    return True

def main():
    try:
        if not verify_edge_cases():
            print(0)
            return
        corpus = make_corpus()
        comp = squeeze.compress(corpus)
        if not isinstance(comp, (bytes, bytearray)):
            print(0)
            return
        decomp = squeeze.decompress(comp)
        if decomp != corpus or len(comp) == 0:
            print(0)
            return
        ratio = len(corpus) / len(comp)
        print(f"{ratio:.6f}")
    except Exception:
        print(0)

if __name__ == "__main__":
    main()
