import random, sys

# Generate ~20MB of realistic-ish text with various punctuation, cases, numbers, and ties
random.seed(42)
vocab = [f"word{i}" for i in range(500)] + [f"Common{i}" for i in range(50)] + ["Apple", "apple", "APPLE", "banana", "Banana", "cherry", "date", "elderberry", "fig", "grape"]
# Make some exact ties
# Let's generate ~1MB block and repeat it 20 times, plus some extra words for exact ties
words = [random.choice(vocab) for _ in range(150000)]
sep = [" ", " ", " ", "\n", ", ", ". ", "! ", "? ", "; ", " - ", "123 ", "\t"]
chunk = "".join(w + random.choice(sep) for w in words)
text = chunk * 20
# Add specific high-frequency tie words
tie_chunk = ("zettaword " * 50000) + ("alphaword " * 50000) + ("betaword " * 50000) + "\n"
with open("input20m.txt", "wb") as f:
    f.write(text.encode('ascii'))
    f.write(tie_chunk.encode('ascii'))

