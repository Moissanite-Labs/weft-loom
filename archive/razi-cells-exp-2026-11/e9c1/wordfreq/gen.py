import random

vocab = [
    "the", "of", "and", "to", "in", "a", "is", "that", "for", "it",
    "as", "was", "with", "be", "by", "on", "not", "he", "i", "this",
    "are", "or", "his", "from", "at", "which", "but", "have", "an", "had",
    "they", "you", "were", "their", "one", "all", "we", "can", "her", "has",
    "there", "been", "if", "more", "when", "will", "would", "who", "so", "no"
] + [f"word{chr(97 + i//26)}{chr(97 + i%26)}" for i in range(600)]

random.seed(42)
weights = [1000 // (i + 10) for i in range(len(vocab))]
# Ensure exact tie in top 10
picked = random.choices(vocab, weights=weights, k=50000)
# Mix casing and whitespace/newlines
lines = []
for i in range(0, len(picked), 12):
    w_slice = picked[i:i+12]
    if i % 24 == 0:
        w_slice[0] = w_slice[0].capitalize()
    if i % 48 == 0:
        w_slice[-1] = w_slice[-1].upper()
    lines.append(" ".join(w_slice))
chunk = "\n".join(lines) + "\n"

with open("input20mb.txt", "w") as f:
    while f.tell() < 20 * 1024 * 1024:
        f.write(chunk)
