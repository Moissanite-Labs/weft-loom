import random
import time
import fibmod

MOD = 10**9 + 7
F = fibmod.fib


def _ref(n):
    """Independent reference: 2x2 matrix power."""
    def mul(A, B):
        return ((A[0]*B[0] + A[1]*B[2]) % MOD, (A[0]*B[1] + A[1]*B[3]) % MOD,
                (A[2]*B[0] + A[3]*B[2]) % MOD, (A[2]*B[1] + A[3]*B[3]) % MOD)
    R = (1, 0, 0, 1)
    A = (1, 1, 1, 0)
    while n:
        if n & 1:
            R = mul(R, A)
        A = mul(A, A)
        n >>= 1
    return R[1]


def fail():
    print(0)
    raise SystemExit


# small values vs naive iteration
a, b = 0, 1
small = []
for i in range(200):
    small.append(a % MOD)
    a, b = b, a + b
for i, want in enumerate(small):
    if F(i) != want:
        fail()

# big / random values vs independent matrix reference
rng = random.Random(12345)
tests = [200, 10**6, 10**9, 10**18, 10**18 - 1, (1 << 59), (1 << 60) - 1]
tests += [rng.randrange(10**18) for _ in range(60)]
for n in tests:
    if F(n) != _ref(n):
        fail()

N = 250000
nums = [rng.randrange(10**18) for _ in range(N)]
best = None
for _ in range(3):
    start = time.perf_counter()
    acc = 0
    for n in nums:
        acc ^= F(n)
    elapsed = time.perf_counter() - start
    if best is None or elapsed < best:
        best = elapsed
print(N / best)
