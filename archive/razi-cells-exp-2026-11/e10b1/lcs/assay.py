import random, subprocess, sys, time
sys.path.insert(0, '.')
def dp(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]
def cli(inp):
    return subprocess.run([sys.executable, 'lcs.py'], input=inp, capture_output=True, text=True, timeout=20).stdout.strip()
def fail():
    print(0)
    sys.exit(0)
try:
    big = open('big.txt').read()
    exp = open('big.exp').read().strip()
    if cli(big) != exp: fail()
    rnd = random.Random(7)
    for k, n in [(2, 300), (4, 250), (26, 300), (1, 50), (3, 0)]:
        al = 'abcdefghijklmnopqrstuvwxyz'[:k]
        a = ''.join(rnd.choice(al) for _ in range(n))
        b = ''.join(rnd.choice(al) for _ in range(rnd.randint(0, 300)))
        if cli(a + '\n' + b + '\n') != str(dp(a, b)): fail()
    if cli('AGGTAB\nGXTXAYB') != '4': fail()
    from lcs import lcs
    a, b = big.split('\n')[:2]
    e = int(exp)
    best = 1e9
    for _ in range(5):
        t = time.perf_counter()
        for _ in range(100):
            if lcs(a, b) != e: fail()
        best = min(best, time.perf_counter() - t)
    print(round(100 / best, 1))
except SystemExit:
    raise
except Exception:
    print(0)
