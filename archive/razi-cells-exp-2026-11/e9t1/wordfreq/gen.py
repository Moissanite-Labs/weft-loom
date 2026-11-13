import random, re
from collections import Counter

random.seed(42)
# Generate vocabulary of ~1000 words of length 2-12, plus some uppercase and punctuation
alpha = "abcdefghijklmnopqrstuvwxyz"
vocab = ["".join(random.choices(alpha, k=random.randint(2, 10))) for _ in range(1000)]
# Zipf-like weights
weights = [1.0 / (i + 1) ** 0.8 for i in range(1000)]

# Generate blocks and repeat/mix to reach ~20MB fast
chunk_words = random.choices(vocab, weights=weights, k=50000)
# Add some capitalization and punctuation
lines = []
for i in range(0, 50000, 12):
    w = chunk_words[i:i+12]
    w[0] = w[0].capitalize()
    if i % 24 == 0:
        w[-1] = w[-1].upper() + "!"
    else:
        w[-1] = w[-1] + ",."
    lines.append(" ".join(w))
block = "\n".join(lines) + "\n"
# Repeat block with slight permutations to hit ~20MB
with open("input.txt", "w") as f:
    size = 0
    while size < 20_000_000:
        f.write(block)
        size += len(block)

# Compute ground truth using standard regex [a-z]+ on lowercased text, and check if whitespace/translate matches
with open("input.txt", "r") as f:
    text = f.read()

words_re = re.findall(r'[a-z]+', text.lower())
counts_re = Counter(words_re)
top10_re = sorted(counts_re.items(), key=lambda x: (-x[1], x[0]))[:10]
with open("expected.txt", "w") as f:
    for w, c in top10_re:
        f.write(f"{w} {c}\n")

print("Size:", len(text))
print("Top 10:")
for w, c in top10_re:
    print(f"{w} {c}")
