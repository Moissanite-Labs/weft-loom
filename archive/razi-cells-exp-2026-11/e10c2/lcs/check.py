import random, subprocess, sys, time

def ref(a, b):
    prev = [0]*(len(b)+1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j]+1 if x == y else max(prev[j+1], cur[j]))
        prev = cur
    return prev[-1]

def run(a, b):
    out = subprocess.run([sys.executable, 'lcs.py'], input=(a+'\n'+b+'\n').encode(), capture_output=True)
    return int(out.stdout.decode().strip())

random.seed(1)
cases = [('', ''), ('a', ''), ('abc', 'abc'), ('abc', 'xyz'), ('AGGTAB', 'GXTXAYB')]
for _ in range(30):
    n = random.randint(0, 60); m = random.randint(0, 60)
    k = random.choice([2, 4, 26])
    cases.append((''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(n)),
                  ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(m))))
for a, b in cases:
    r = ref(a, b); g = run(a, b)
    if r != g:
        print('MISMATCH', repr(a), repr(b), r, g); sys.exit(1)
# timing on 3000-char strings
a = ''.join(random.choice('ACGT') for _ in range(3000))
b = ''.join(random.choice('ACGT') for _ in range(3000))
t = time.time(); g = run(a, b); dt = time.time()-t
print('ok', g, 'time', round(dt, 3))
