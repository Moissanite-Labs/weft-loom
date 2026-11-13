import random, subprocess, sys, time

def ref(a, b):
    prev = [0]*(len(b)+1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j]+1 if x == y else max(prev[j+1], cur[j]))
        prev = cur
    return prev[-1]

def run(inp):
    out = subprocess.run([sys.executable, 'lcs.py'], input=inp.encode(), capture_output=True)
    return out.stdout.decode().strip()

random.seed(7)
# correctness on small cases
for _ in range(12):
    n = random.randint(0, 80); m = random.randint(0, 80)
    k = random.choice([2, 4, 26])
    a = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(n))
    b = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(m))
    if str(ref(a, b)) != run(a+'\n'+b+'\n'):
        print(0); sys.exit(0)
# one fixed 3000-case with known answer (from check.py seed path)
random.seed(1)
# heavy timing: many big pairs
pairs = []
for _ in range(8):
    n = random.randint(2500, 3000); m = random.randint(2500, 3000)
    k = random.choice([2, 4, 26])
    pairs.append(''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(n)) + '\n' +
                 ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'[:k]) for _ in range(m)) + '\n')
t = time.time()
for p in pairs:
    for _ in range(3):
        r = run(p)
        if not r.isdigit():
            print(0); sys.exit(0)
dt = time.time() - t
print(round(1000.0/dt, 2))
