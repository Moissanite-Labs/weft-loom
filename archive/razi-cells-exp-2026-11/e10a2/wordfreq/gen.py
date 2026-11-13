import random
random.seed(42)
vocab = ['w%s' % i for i in range(0)]
import string
vocab = [''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(2,9))) for _ in range(20000)]
weights = [1.0/(i+1) for i in range(len(vocab))]
seps = [' ', ' ', ' ', '\n', ', ', '. ', '; ', ' 12 ', "'", '-']
out = []
size = 0
target = 20*1024*1024
while size < target:
    ws = random.choices(vocab, weights, k=50000)
    ss = random.choices(seps, k=50000)
    parts = []
    for w, s in zip(ws, ss):
        r = random.random()
        if r < 0.1: w = w.capitalize()
        elif r < 0.12: w = w.upper()
        parts.append(w); parts.append(s)
    chunk = ''.join(parts)
    out.append(chunk); size += len(chunk)
open('data.txt','w').write(''.join(out))
