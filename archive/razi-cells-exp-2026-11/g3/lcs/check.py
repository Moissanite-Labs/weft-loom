import random, sys
sys.path.insert(0, '.')
from lcs import lcs_length

def dp(a, b):
    if len(a) < len(b): a, b = b, a
    prev = [0]*(len(b)+1)
    for ch in a:
        cur = [0]*(len(b)+1)
        for j, c in enumerate(b):
            cur[j+1] = prev[j]+1 if ch == c else (cur[j] if cur[j] > prev[j+1] else prev[j+1])
        prev = cur
    return prev[-1]

random.seed(1)
bad = 0
for t in range(2000):
    n = random.randint(0, 8); m = random.randint(0, 8)
    k = random.choice([1, 2, 3, 4])
    a = bytes(random.randrange(97, 97+k) for _ in range(n))
    b = bytes(random.randrange(97, 97+k) for _ in range(m))
    got, exp = lcs_length(a, b), dp(a, b)
    if got != exp:
        bad += 1
        if bad < 6: print("MISMATCH", a, b, got, exp)
print("bad:", bad, "of 2000")
