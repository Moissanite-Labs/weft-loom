import random, subprocess, sys, time
from bisect import bisect_left


def dp(a, b):
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = cur[j - 1] if cur[j - 1] > prev[j] else prev[j]
        prev = cur
    return prev[len(b)]


def hs(a, b):
    pos = {}
    for i, ch in enumerate(a):
        pos.setdefault(ch, []).append(i)
    tails = []
    for ch in b:
        for i in reversed(pos.get(ch, ())):
            k = bisect_left(tails, i)
            if k == len(tails):
                tails.append(i)
            else:
                tails[k] = i
    return len(tails)


def run(a, b):
    p = subprocess.run([sys.executable, 'lcs.py'],
                       input=(a + '\n' + b + '\n').encode(),
                       capture_output=True, timeout=120)
    return p.stdout.decode().strip()


rnd = random.Random(12345)
ok = True
for t in range(25):
    n = rnd.randint(0, 40)
    m = rnd.randint(0, 40)
    a = ''.join(rnd.choice('abcde') for _ in range(n))
    b = ''.join(rnd.choice('abcde') for _ in range(m))
    got = run(a, b)
    exp = dp(a, b)
    if got != str(exp):
        print('FAIL small', repr(a), repr(b), got, exp, file=sys.stderr)
        ok = False
        break

A = ''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(3000))
B = ''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(3000))

if ok:
    exp = hs(A, B)
    got = run(A, B)
    if got != str(exp):
        print('FAIL big', got, exp, file=sys.stderr)
        ok = False

if ok:
    best = 1e9
    for _ in range(3):
        t0 = time.perf_counter()
        got = run(A, B)
        dt = time.perf_counter() - t0
        if got != str(exp):
            print('FAIL timing run', got, exp, file=sys.stderr)
            ok = False
            break
        best = min(best, dt)

print(1.0 / best if ok else 0)
