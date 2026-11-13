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
    "system", "network", "database", "process", "message", "service", "request",
    "response", "status", "error", "configuration", "application", "performance",
    "information", "development", "management", "environment", "architecture"
]

def make_corpus():
    rng = random.Random(42)
    samples = []

    # 1. English-like paragraphs with Markov-ish / Zipfian structure and repeated phrases
    phrases = [
        " ".join(rng.choices(WORDS, k=rng.randint(4, 10)))
        for _ in range(80)
    ]
    weights = [1.0 / ((i + 1) ** 0.8) for i in range(len(WORDS))]
    for _ in range(15):
        paras = []
        for _ in range(25):
            sentences = []
            for _ in range(rng.randint(4, 9)):
                if rng.random() < 0.35:
                    s = rng.choice(phrases) + " " + " ".join(rng.choices(WORDS, weights=weights, k=rng.randint(5, 12)))
                else:
                    s = " ".join(rng.choices(WORDS, weights=weights, k=rng.randint(8, 20)))
                sentences.append(s.capitalize() + ".")
            paras.append(" ".join(sentences))
        samples.append("\n\n".join(paras).encode("utf-8"))

    # 2. Structured JSON records (API payloads, logs, nested configs)
    for batch in range(15):
        records = []
        for i in range(60):
            rec = {
                "id": i + batch * 1000,
                "timestamp": f"2025-03-{(i % 28) + 1:02d}T{(i % 24):02d}:{(i * 7) % 60:02d}:00Z",
                "service": rng.choice(["auth-service", "payment-gateway", "user-profile", "search-index", "notification-worker"]),
                "level": rng.choice(["INFO", "INFO", "INFO", "WARN", "ERROR", "DEBUG"]),
                "status_code": rng.choice([200, 200, 200, 201, 204, 400, 404, 500]),
                "latency_ms": round(rng.uniform(1.5, 250.0), 2),
                "user": {
                    "user_id": f"usr_{rng.randint(1000, 1200)}",
                    "role": rng.choice(["admin", "member", "guest", "viewer"]),
                    "active": rng.choice([True, True, False]),
                    "tags": rng.sample(["beta", "enterprise", "verified", "internal", "legacy", "v2"], k=rng.randint(1, 4))
                },
                "message": rng.choice(phrases) + " (" + " ".join(rng.choices(WORDS, weights=weights, k=6)) + ")",
            }
            records.append(rec)
        samples.append(json.dumps({"batch": batch, "records": records}, indent=2).encode("utf-8"))

    # 3. Combined mixed document
    combined = b"\n---SECTION---\n".join(samples[:6] + samples[15:21])
    samples.append(combined)

    return samples

EDGE_CASES = [
    b"",
    b"a",
    b"\x00\xff\x00\xff" * 100,
    bytes(range(256)) * 4,
    b'{"hello": "world", "numbers": [1, 2, 3, 4, 5]}',
]

def main():
    samples = make_corpus()
    for edge in EDGE_CASES:
        c = squeeze.compress(edge)
        if not isinstance(c, (bytes, bytearray)) or bytes(squeeze.decompress(c)) != edge:
            print(0)
            return

    total_orig = 0
    total_comp = 0
    for s in samples:
        c = squeeze.compress(s)
        if not isinstance(c, (bytes, bytearray)):
            print(0)
            return
        d = squeeze.decompress(c)
        if d != s:
            print(0)
            return
        total_orig += len(s)
        total_comp += len(c)

    ratio = total_orig / max(1, total_comp)
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
