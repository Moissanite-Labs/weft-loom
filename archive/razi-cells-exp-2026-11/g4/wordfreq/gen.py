import random, sys

# deterministic ~20MB of lowercased-ish text with punctuation, unicode, mixed case
seed = 12345
rnd = random.Random(seed)
common = ["the", "of", "and", "to", "in", "a", "is", "that", "it", "for",
          "was", "as", "with", "be", "by", "on", "not", "he", "i", "this"]
extra = ["".join(rnd.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rnd.randint(1, 12)))
         for _ in range(3000)]
punct = [" ", " ", " ", " ", ", ", ". ", "; ", "\t", "\n", "! ", " (", ") ", "-", "'s "]
words = []
n = 0
target = 20 * 1024 * 1024
out = []
while n < target:
    r = rnd.random()
    if r < 0.55:
        w = rnd.choice(common)
    elif r < 0.6:
        w = rnd.choice(common).upper() if rnd.random() < 0.5 else rnd.choice(common)
    else:
        w = rnd.choice(extra)
    p = rnd.choice(punct)
    s = w + p
    out.append(s)
    n += len(s)
sys.stdout.write("".join(out))
