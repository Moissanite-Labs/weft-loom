import random
import json
import time
import squeeze

def generate_corpus():
    rng = random.Random(42)
    
    # English-like text generator (Markov / vocabulary with realistic distribution & phrases)
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
        "system", "information", "data", "compression", "algorithm", "network", "process",
        "memory", "performance", "structure", "function", "application", "development",
        "management", "experience", "technology", "international", "organization",
        "environment", "communication", "understanding", "relationship", "administration"
    ]
    weights = [1000 / ((i + 5) ** 1.1) for i in range(len(words))]
    
    phrases = [
        "in the middle of the ", "as a matter of fact ", "on the other hand ",
        "for the purpose of ", "at the same time ", "with respect to the ",
        "it is important to note that ", "as a result of the ",
        "in accordance with the ", "under the circumstances "
    ]
    
    text_parts = []
    for _ in range(350):
        sentence_len = rng.randint(8, 25)
        sent = rng.choices(words, weights=weights, k=sentence_len)
        sent[0] = sent[0].capitalize()
        s = " ".join(sent)
        if rng.random() < 0.3:
            s = rng.choice(phrases).capitalize() + s.lower()
        if rng.random() < 0.2:
            s += ", " + " ".join(rng.choices(words, weights=weights, k=rng.randint(4, 10)))
        s += rng.choice([". ", ". ", ". ", "! ", "? ", ".\n"])
        text_parts.append(s)
    english_text = "".join(text_parts)
    
    # JSON data generator (realistic API records, nested objects, arrays, numbers, timestamps, statuses)
    records = []
    statuses = ["active", "pending", "archived", "deleted", " suspended"]
    roles = ["admin", "editor", "viewer", "billing", "developer", "support"]
    tags_pool = ["urgent", "production", "staging", "internal", "external", "v1", "v2", "deprecated", "verified"]
    regions = ["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1", "sa-east-1"]
    
    for i in range(400):
        rec = {
            "id": f"usr_{100000 + i:06d}",
            "index": i,
            "isActive": rng.choice([True, False, True]),
            "status": rng.choice(statuses),
            "balance": round(rng.uniform(10.0, 99999.99), 2),
            "age": rng.randint(18, 75),
            "role": rng.choice(roles),
            "region": rng.choice(regions),
            "email": f"user{i}.{rng.choice(words[:40])}@example.{rng.choice(['com', 'org', 'net', 'io'])}",
            "created_at": f"202{rng.randint(0,4)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z",
            "tags": rng.sample(tags_pool, k=rng.randint(1, 4)),
            "metrics": {
                "login_count": rng.randint(0, 5000),
                "latency_ms": round(rng.uniform(1.5, 250.0), 3),
                "error_rate": round(rng.uniform(0.0, 0.05), 4),
                "quota_used": rng.randint(1024, 10485760)
            },
            "description": " ".join(rng.choices(words, weights=weights, k=rng.randint(6, 18))) + "."
        }
        records.append(rec)
    
    json_text = json.dumps({"version": "2.4.0", "count": len(records), "data": records}, indent=2)
    
    # Combined corpus + individual payloads for multi-block testing
    combined = (english_text + "\n---JSON_START---\n" + json_text).encode("utf-8")
    eng_bytes = english_text.encode("utf-8")
    json_bytes = json_text.encode("utf-8")
    return [combined, eng_bytes, json_bytes, b"", b"a", b"hello world! " * 100, bytes(range(256)) * 4]

def main():
    payloads = generate_corpus()
    total_raw = 0
    total_comp = 0
    
    # Repeat enough times or use main corpus so workload takes ~0.3-1.5s
    main_payloads = payloads[:3]
    edge_payloads = payloads[3:]
    
    try:
        # Check edge cases first
        for p in edge_payloads:
            c = squeeze.compress(p)
            if not isinstance(c, bytes):
                print(0)
                return
            d = squeeze.decompress(c)
            if d != p:
                print(0)
                return
        
        # Run main corpus
        t0 = time.perf_counter()
        iters = 3
        for _ in range(iters):
            for p in main_payloads:
                c = squeeze.compress(p)
                if not isinstance(c, bytes):
                    print(0)
                    return
                d = squeeze.decompress(c)
                if d != p:
                    print(0)
                    return
                total_raw += len(p)
                total_comp += len(c)
        
        ratio = total_raw / total_comp
        print(f"{ratio:.6f}")
    except Exception:
        print(0)

if __name__ == "__main__":
    main()
