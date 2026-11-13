import random, sys, time
sys.path.insert(0, '.')
from lcs import lcs_length

def dp(a, b):
    m = len(b)
    prev = [0]*(m+1)
    for i in range(1, len(a)+1):
        cur = [0]*(m+1)
        ai = a[i-1]
        for j in range(1, m+1):
            if ai == b[j-1]:
                cur[j] = prev[j-1] + 1
            else:
                x = prev[j]
                y = cur[j-1]
                cur[j] = x if x > y else y
        prev = cur
    return prev[m]

random.seed(1)
for t in range(300):
    n = random.randint(0, 40)
    k = random.randint(0, 40)
    a = ''.join(random.choice('abc') for _ in range(n))
    b = ''.join(random.choice('abc') for _ in range(k))
    e = dp(a, b)
    g = lcs_length(a, b)
    if e != g:
        print('FAIL', repr(a), repr(b), e, g)
        sys.exit(1)
print('correctness OK')

a = ''.join(random.choice('abcdefghij') for _ in range(3000))
b = ''.join(random.choice('abcdefghij') for _ in range(3000))
t0 = time.time()
r = lcs_length(a, b)
dt = time.time() - t0
print('3000x3000 result', r, 'time', round(dt, 4))
print('score', round(1.0/dt, 3))
