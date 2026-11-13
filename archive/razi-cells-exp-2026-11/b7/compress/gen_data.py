"""Deterministic fixed benchmark corpus: English-like prose mixed with compact JSON."""
import json, random

SEED = 0x5EE2E
ADJ = ["quiet", "bright", "careful", "modest", "rapid", "gentle", "curious", "steady", "complex", "simple", "distant", "golden", "noisy", "patient", "reliable", "subtle", "modern", "local", "global", "seasonal"]
NOUN = ["engineer", "garden", "report", "server", "river", "market", "letter", "sensor", "library", "meeting", "schedule", "cluster", "window", "model", "packet", "invoice", "notebook", "bridge", "channel", "process"]
VERB = ["observes", "updates", "measures", "reviews", "connects", "collects", "describes", "protects", "summarizes", "indexes", "validates", "repairs", "compares", "records", "routes", "explains", "monitors", "restores", "builds", "tracks"]
ADV = ["slowly", "briefly", "carefully", "regularly", "quietly", "rapidly", "clearly", "locally", "remotely", "daily", "accurately", "smoothly", "gradually", "manually", "automatically", "occasionally"]
PLACE = ["north station", "old harbor", "central office", "small village", "data center", "east wing", "city archive", "research lab", "main terminal", "river bank", "regional hub", "cloud region"]
NAME = ["Alice", "Ben", "Clara", "Dmitri", "Elena", "Farid", "Grace", "Hiro", "Iris", "Jonas", "Keiko", "Liam", "Maya", "Noah", "Olivia", "Priya", "Quinn", "Rosa", "Samir", "Tessa"]
TOPIC = ["temperature readings", "inventory counts", "network latency", "customer feedback", "batch results", "access logs", "policy updates", "delivery routes", "weekly summaries", "quality checks", "training examples", "storage usage"]
CLAUSE = ["while the dashboard remained responsive", "because the previous batch had finished", "after the operators approved the change", "before the next maintenance window", "although the signal was weaker than expected", "so the archive could be updated", "when the validation job returned", "and the final totals agreed", "unless the queue grew too large", "with only minor differences from yesterday"]
TEMPLATES = [
    "the {adj} {noun} {verb} the {topic} {adv} near the {place}",
    "{name} {verb} a {adj} {noun} for the {topic} each morning",
    "a {adj} {noun} can {base} the {topic} without delaying the {place}",
    "operators in the {place} {base} several {noun} entries during the {adj} review",
    "the {topic} from the {adj} {noun} looked consistent after a {adv} check",
    "we {base} the {noun}, then {base} the {topic} near the {place}",
    "{name} said that the {adj} {noun} would {base} the next {topic}",
    "in the {place}, the {noun} {verb} every {topic} {adv}",
]
BASE = ["review", "update", "collect", "compare", "summarize", "validate", "record", "route", "monitor", "restore", "index", "explain"]
STATUS = ["ok", "pending", "retry", "complete", "failed", "queued", "cached", "verified"]
ACTION = ["login", "purchase", "refresh", "upload", "download", "validate", "archive", "restore", "update", "sync", "publish", "rotate"]
REGION = ["us-east", "us-west", "eu-central", "eu-west", "ap-south", "ap-east", "local-edge", "backup-zone"]
DEVICE = ["desktop", "tablet", "phone", "sensor", "gateway", "printer", "scanner", "laptop"]
TAG = ["alpha", "beta", "gamma", "delta", "pilot", "stable", "urgent", "routine", "nightly", "audit", "sample", "cached"]
MSG = [
    "the record was accepted by the validation worker",
    "the queue completed without retrying the request",
    "the summary matched the expected regional totals",
    "the operator confirmed the delayed batch result",
    "the sensor reported a stable temperature range",
    "the archive indexed the document after review",
    "the dashboard displayed the latest hourly counts",
    "the service restored the cached configuration",
]

def sentence(r):
    t = r.choice(TEMPLATES)
    s = t.format(adj=r.choice(ADJ), noun=r.choice(NOUN), verb=r.choice(VERB),
                 adv=r.choice(ADV), place=r.choice(PLACE), name=r.choice(NAME),
                 topic=r.choice(TOPIC), base=r.choice(BASE))
    if r.random() < 0.62:
        s += " " + r.choice(CLAUSE)
    s = s[0].upper() + s[1:] + r.choice([".", ".", ".", "!", "?"])
    return s

def text_doc(r, i):
    paras = []
    for p in range(3):
        paras.append(" ".join(sentence(r) for _ in range(12)))
    return ("\n\n".join(paras) + "\n").encode("ascii")

def record(r, i, j):
    month = 1 + (i + j) % 12
    day = 1 + (i * 7 + j * 3) % 28
    hour = (i * 5 + j * 2) % 24
    minute = (i * 11 + j * 7) % 60
    second = (i * 13 + j * 17) % 60
    return {
        "id": 100000 + i * 100 + j,
        "timestamp": f"2024-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z",
        "user": r.choice(NAME).lower() + str((i + j) % 97),
        "action": r.choice(ACTION),
        "status": r.choice(STATUS),
        "region": r.choice(REGION),
        "device": r.choice(DEVICE),
        "amount": round(r.random() * 1000, 2),
        "active": bool((i + j) % 2),
        "tags": [r.choice(TAG) for _ in range(3)],
        "metadata": {
            "score": (i * 31 + j * 17) % 1000,
            "retry": (i + j) % 5,
            "note": r.choice(MSG),
            "origin": r.choice(PLACE),
            "checksum": None if (i + j) % 7 == 0 else f"{i:04x}{j:04x}{r.randrange(256):02x}",
        },
    }

def json_doc(r, i):
    obj = {
        "dataset": "mixed-events",
        "batch": i,
        "generated_by": "squeeze-benchmark",
        "records": [record(r, i, j) for j in range(30)],
    }
    return json.dumps(obj, separators=(",", ":")).encode("ascii")

def make_docs(n=64):
    r = random.Random(SEED)
    docs = []
    for i in range(n):
        docs.append(json_doc(r, i) if i % 2 else text_doc(r, i))
    return docs

def make_corpus(n=64):
    return b"\n".join(make_docs(n))
