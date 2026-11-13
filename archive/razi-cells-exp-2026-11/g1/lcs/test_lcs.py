import random, sys
sys.path.insert(0, '.')
from lcs import lcs_len

def dp(a, b):
    if not a or not b: return 0
    prev = [0]*(len(b)+1)
    for ca in a:
        cur = [0]*(len(b)+1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j-1] + 1
            else:
                cur[j] = max(prev[j], cur[j-1])
        prev = cur
    return prev[-1]

random.seed(1)
for _ in range(300):
    n = random.randint(0, 30)
    m = random.randint(0, 30)
    al = 'abc'
    a = ''.join(random.choice(al) for _ in range(n))
    b = ''.join(random.choice(al) for _ in range(m))
    got = lcs_len(a, b)
    exp = dp(a, b)
    if got != exp:
        print('FAIL', repr(a), repr(b), got, exp)
        sys.exit(1)
print('OK')
