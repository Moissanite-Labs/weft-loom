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
                x = cur[j - 1]
                y = prev[j]
                cur[j] = x if x > y else y
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
    if p.returncode != 0:
        print('CRASH', p.stderr.decode()[:500], file=sys.stderr)
        return None
    return p.stdout.decode().strip()


ok = True
rnd = random.Random(12345)

# 1. exhaustive-ish small tests vs DP, several alphabet sizes
for alpha in ('ab', 'abc', 'abcde', 'abcdefghij'):
    for _ in range(60):
        n = rnd.randint(0, 30)
        m = rnd.randint(0, 30)
        a = ''.join(rnd.choice(alpha) for _ in range(n))
        b = ''.join(rnd.choice(alpha) for _ in range(m))
        got = run(a, b)
        exp = str(dp(a, b))
        if got != exp:
            print('FAIL small', alpha, repr(a), repr(b), got, exp, file=sys.stderr)
            ok = False
            break
    if not ok:
        break

# 2. edge cases
for a, b, exp in [('', '', '0'), ('abc', '', '0'), ('', 'abc', '0'),
                  ('abc', 'abc', '3'), ('aaa', 'aa', '2'),
                  ('a' * 3000, 'a' * 3000, '3000'),
                  ('a' * 3000, 'b' * 3000, '0'),
                  ('abc', 'cba', '1')]:
    if not ok:
        break
    got = run(a, b)
    if got != exp:
        print('FAIL edge', len(a), len(b), got, exp, file=sys.stderr)
        ok = False

# 3. medium/large cross-check vs independent Hunt-Szymanski
for n, alpha in ((200, 'abc'), (500, 'abcde'), (3000, 'abcdefghijklmnopqrstuvwxyz'),
                 (3000, 'abcd'), (3000, 'ab')):
    if not ok:
        break
    a = ''.join(rnd.choice(alpha) for _ in range(n))
    b = ''.join(rnd.choice(alpha) for _ in range(n))
    exp = str(hs(a, b))
    got = run(a, b)
    if got != exp:
        print('FAIL big', n, alpha[:5], got, exp, file=sys.stderr)
        ok = False

if not ok:
    print(0)
    sys.exit(0)

# 4. timing on the 3000-char workload (fitness: 1/seconds)
A = ''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(3000))
B = ''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(3000))
exp = str(hs(A, B))
best = 1e9
for _ in range(5):
    t0 = time.perf_counter()
    got = run(A, B)
    dt = time.perf_counter() - t0
    if got != exp:
        print('FAIL timing', got, exp, file=sys.stderr)
        print(0)
        sys.exit(0)
    best = min(best, dt)

# alternative algorithm timing for the divide decision
t0 = time.perf_counter()
hsres = hs(A, B)
hs_dt = time.perf_counter() - t0
print('bitparallel %.4fs  hunt-szymanski %.4fs  (lcs=%d)' % (best, hs_dt, hsres), file=sys.stderr)
print(1.0 / best)
