import json
import random
import time
import squeeze

def make_corpus() -> list[bytes]:
    rng = random.Random(42)
    
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "system", "network", "database", "compression", "algorithm", "performance",
        "dictionary", "entropy", "encoding", "transform", "structure", "message",
        "request", "response", "header", "payload", "timestamp", "identifier",
        "configuration", "parameter", "value", "string", "integer", "boolean",
        "service", "cluster", "instance", "node", "memory", "storage", "compute",
        "application", "interface", "protocol", "transaction", "record", "field",
        "context", "execution", "pipeline", "process", "thread", "worker", "queue"
    ]
    
    # 1. English-like articles / prose
    paragraphs = []
    for _ in range(300):
        sentences = []
        for _ in range(rng.randint(4, 10)):
            length = rng.randint(6, 22)
            sent_words = [rng.choice(words) for _ in range(length)]
            sent_words[0] = sent_words[0].capitalize()
            sentences.append(" ".join(sent_words) + rng.choice([".", ".", ".", "!", "?"]))
        paragraphs.append(" ".join(sentences))
    english_text = "\n\n".join(paragraphs).encode("utf-8")
    
    # 2. Structured JSON records (API logs / nested objects)
    records = []
    for i in range(600):
        rec = {
            "id": f"rec_{i:06d}",
            "timestamp": f"2025-03-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z",
            "active": rng.choice([True, False]),
            "score": round(rng.uniform(0.0, 1000.0), 4),
            "count": rng.randint(0, 50000),
            "tags": [rng.choice(words) for _ in range(rng.randint(1, 6))],
            "user": {
                "uid": rng.randint(1000, 9999),
                "name": f"{rng.choice(words).capitalize()} {rng.choice(words).capitalize()}",
                "role": rng.choice(["admin", "editor", "viewer", "guest"]),
                "preferences": {
                    "theme": rng.choice(["dark", "light", "system"]),
                    "notifications": rng.choice([True, False]),
                    "retries": rng.randint(1, 5)
                }
            },
            "message": " ".join(rng.choice(words) for _ in range(rng.randint(8, 25)))
        }
        records.append(rec)
    json_pretty = json.dumps({"status": "ok", "total": len(records), "data": records}, indent=2).encode("utf-8")
    json_lines = "\n".join(json.dumps(r) for r in records).encode("utf-8")
    
    # 3. Mixed document (Markdown + JSON blocks + prose)
    mixed_parts = []
    for i in range(100):
        mixed_parts.append(f"# Section {i}: {paragraphs[i % len(paragraphs)][:80]}\n\n")
        mixed_parts.append(paragraphs[(i * 3) % len(paragraphs)] + "\n\n")
        mixed_parts.append("```json\n" + json.dumps(records[i * 2], indent=2) + "\n```\n\n")
    mixed_blob = "".join(mixed_parts).encode("utf-8")

    return [english_text, json_pretty, json_lines, mixed_blob, english_text + b"\n" + json_pretty]

def main():
    # Edge cases check
    edge_cases = [b"", b"a", b"\x00\xff\x00\xfe", b"hello world" * 100, bytes(range(256)) * 4]
    for ec in edge_cases:
        c = squeeze.compress(ec)
        if not isinstance(c, (bytes, bytearray)) or squeeze.decompress(bytes(c)) != ec:
            print(0)
            return

    corpus = make_corpus()
    total_raw = 0
    total_comp = 0
    for blob in corpus:
        c = squeeze.compress(blob)
        if not isinstance(c, (bytes, bytearray)):
            print(0)
            return
        d = squeeze.decompress(bytes(c))
        if d != blob:
            print(0)
            return
        total_raw += len(blob)
        total_comp += len(c)

    ratio = total_raw / total_comp
    print(f"{ratio:.6f}")

if __name__ == "__main__":
    main()
