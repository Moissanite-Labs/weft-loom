import json
import random
import time
import squeeze

WORDS = [
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
    "system", "network", "protocol", "message", "client", "server", "database", "query",
    "response", "request", "header", "payload", "timestamp", "status", "error", "success",
    "configuration", "parameter", "function", "variable", "object", "array", "string", "number"
]

def make_corpus():
    rng = random.Random(42)
    chunks = []
    
    # Generate English-like paragraphs with Markov-like bias (zipf-ish)
    weights = [100.0 / ((i + 1) ** 0.8) for i in range(len(WORDS))]
    for _ in range(300):
        sent_len = rng.randint(8, 25)
        words = rng.choices(WORDS, weights=weights, k=sent_len)
        words[0] = words[0].capitalize()
        sentence = " ".join(words) + rng.choice([". ", ". ", ". ", "! ", "? ", ".\n"])
        chunks.append(sentence.encode("utf-8"))
        
    # Generate structured JSON records
    records = []
    for i in range(400):
        rec = {
            "id": i,
            "uuid": f"user-{rng.randint(1000, 9999)}-{i:04d}",
            "active": rng.choice([True, False]),
            "role": rng.choice(["admin", "editor", "viewer", "guest"]),
            "score": round(rng.uniform(0, 1000), 2),
            "tags": rng.sample(WORDS[:40], k=rng.randint(2, 6)),
            "description": " ".join(rng.choices(WORDS, weights=weights, k=rng.randint(10, 30))),
            "meta": {
                "created_at": f"2025-0{rng.randint(1,9)}-{rng.randint(10,28)}T12:00:00Z",
                "retries": rng.randint(0, 5),
                "region": rng.choice(["us-east-1", "eu-west-1", "ap-south-1"])
            }
        }
        records.append(rec)
    chunks.append(json.dumps(records, indent=2).encode("utf-8"))
    
    # Also mixed small blobs and edge cases
    full = b"".join(chunks)
    return full

def main():
    corpus = make_corpus()
    # Test multiple slices + full corpus so workload is ~0.3-1.5s and thorough
    samples = [
        corpus,
        corpus[:len(corpus)//2],
        corpus[len(corpus)//2:],
        b"",
        b"a",
        b"\x00\xff\x00\xff" * 100,
    ]
    total_in = 0
    total_out = 0
    for idx, s in enumerate(samples):
        comp = squeeze.compress(s)
        if not isinstance(comp, (bytes, bytearray)):
            print(0)
            return
        decomp = squeeze.decompress(comp)
        if decomp != s:
            print(0)
            return
        if idx < 3:
            total_in += len(s)
            total_out += len(comp)
    ratio = total_in / max(1, total_out)
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
