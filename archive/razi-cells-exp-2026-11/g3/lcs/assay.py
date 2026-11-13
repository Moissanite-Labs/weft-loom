import random, sys, time, subprocess
sys.path.insert(0, '.')
from lcs import lcs_length as f

def dp(a, b):
    if len(a) < len(b): a, b = b, a
    prev = [0]*(len(b)+1)
    for ch in a:
        cur = [0]*(len(b)+1)
        for j, c in enumerate(b):
            cur[j+1] = prev[j]+1 if ch == c else (cur[j] if cur[j] > prev[j+1] else prev[j+1])
        prev = cur
    return prev[-1]

bad = 0
random.seed(11)
for _ in range(1200):
    n = random.randint(0, 9); m = random.randint(0, 9)
    k = random.choice([1, 2, 3, 5, 26])
    a = bytes(random.randrange(97, 97+k) for _ in range(n))
    b = bytes(random.randrange(97, 97+k) for _ in range(m))
    if f(a, b) != dp(a, b):
        bad += 1
# medium-size reference check (random + near-identical + disjoint)
for (A, B) in [
    (bytes(random.randrange(97, 101) for _ in range(700)), bytes(random.randrange(97, 101) for _ in range(700))),
    (bytes(random.randrange(97, 123) for _ in range(700)), bytes(random.randrange(97, 123) for _ in range(700))),
    (b"ab"*350, b"ba"*350),
    (b"ACGT"*175, b"ACGT"*175),
]:
    if f(A, B) != dp(A, B):
        bad += 1
# CLI end-to-end
r = subprocess.run([sys.executable, 'lcs.py'], input=b"AGGTAB\nGXTXAYB\n", capture_output=True)
if r.returncode != 0 or r.stdout.strip() != b"4":
    bad += 1
if bad:
    print(0)
    sys.exit(0)

random.seed(7)
cases = [
    (bytes(random.randrange(97, 101) for _ in range(3000)), bytes(random.randrange(97, 101) for _ in range(3000))),   # DNA-ish
    (bytes(random.randrange(97, 123) for _ in range(3000)), bytes(random.randrange(97, 123) for _ in range(3000))),  # 26 letters
    (bytes(random.randrange(97, 99) for _ in range(3000)), bytes(random.randrange(97, 99) for _ in range(3000))),    # binary
]
expect = [f(a, b) for a, b in cases]
reps = 0
t = time.perf_counter()
while True:
    for (a, b), e in zip(cases, expect):
        if f(a, b) != e:
            print(0); sys.exit(0)
        reps += 1
    if time.perf_counter() - t > 0.5:
        break
dt = time.perf_counter() - t
print(round(reps/dt, 2))
