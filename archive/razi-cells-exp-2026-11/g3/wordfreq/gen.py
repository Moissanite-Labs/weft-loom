import random, sys

random.seed(1234)
vow = 'aeiou'
con = 'bcdfghjklmnpqrstvwxyz'
vocab = []
for i in range(30000):
    n = random.randint(2, 12)
    vocab.append(''.join(random.choice(vow if j % 2 else con) for j in range(n)))
# zipf-ish weights
weights = [1.0 / (i + 1) ** 1.05 for i in range(len(vocab))]
cum = []
s = 0.0
for w in weights:
    s += w
    cum.append(s)
punct = [', ', '. ', '; ', '! ', '? ', '\n', '\n', ' - ', ' (', ') ', '"', "'"]
target = 20 * 1024 * 1024
out = []
size = 0
bi = 0
while size < target:
    r = random.random() * s
    # binary search
    lo, hi = 0, len(cum) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if cum[mid] < r:
            lo = mid + 1
        else:
            hi = mid
    w = vocab[lo]
    if random.random() < 0.12:
        w = w.capitalize()
    if random.random() < 0.05:
        w = w.upper()
    if random.random() < 0.04:
        w = w + str(random.randint(0, 999))
    out.append(w)
    out.append(random.choice(punct))
    size += len(w) + 2
    bi += 1
    if len(out) > 20000:
        sys.stdout.write(''.join(out))
        out = []
sys.stdout.write(''.join(out))
