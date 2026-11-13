import random

random.seed(42)
# Generate vocabulary with Zipf-like distribution, mixed case, punctuation, digits, whitespace
vocab = []
for i in range(1, 5000):
    w = f"word{chr(97 + (i % 26))}{chr(97 + ((i // 26) % 26))}{chr(97 + ((i // 676) % 26))}"
    if i % 3 == 0:
        w = w.capitalize()
    elif i % 7 == 0:
        w = w.upper()
    vocab.append(w)

# Add some words that tie in count or test alphabetical tie-breaking
weights = [1000.0 / (i + 10) for i in range(len(vocab))]
chunk_words = random.choices(vocab, weights=weights, k=50000)
punct = [" ", " ", " ", ", ", ". ", "! ", "? ", "\n", " - ", " 123 ", " '", "\" "]
block = "".join(w + random.choice(punct) for w in chunk_words)
# Repeat block with slight slices to reach ~20MB
with open("input20m.txt", "wb") as f:
    b = block.encode("ascii")
    target = 20 * 1024 * 1024
    written = 0
    while written + len(b) <= target:
        f.write(b)
        written += len(b)
    f.write(b[:target - written])
print("Generated", written + (target - written), "bytes")
