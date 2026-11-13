import random, sys
random.seed(42)
letters = "abcdefghijklmnopqrstuvwxyz"
vocab = set()
while len(vocab) < 5000:
    vocab.add("".join(random.choice(letters) for _ in range(random.randint(2, 9))))
vocab = sorted(vocab)
weights = [1.0 / (i + 1) for i in range(len(vocab))]
seps = [" ", " ", " ", " ", ", ", ". ", "\n", "; ", " - ", "! ", " 42 "]
target = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000_000
out = []; size = 0
while size < target:
    ws = random.choices(vocab, weights, k=20000)
    for i in range(0, len(ws), 97):
        ws[i] = ws[i].capitalize()
    for i in range(50, len(ws), 211):
        ws[i] = ws[i].upper()
    ss = random.choices(seps, k=20000)
    chunk = "".join(a + b for a, b in zip(ws, ss))
    out.append(chunk); size += len(chunk)
sys.stdout.write("".join(out))
