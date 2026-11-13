import time, random
import fibmod
from fibmod import fib, MOD, PER

def ref(n):
    n %= PER
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (b + b - a) % MOD
        d = (a * a + b * b) % MOD
        if bit == '0': a, b = c, d
        else: a, b = d, (c + d) % MOD
    return a

# sanity of the period
assert ref(0) == 0 and ref(1) == 1
assert ref(PER) == 0 and ref(PER + 1) == 1, "PER is not a period"
assert ref(10) == 55

small = [0, 1]
for i in range(2, 5000):
    small.append((small[-1] + small[-2]) % MOD)
for n in range(5000):
    got = fib(n)
    assert got == small[n], (n, got, small[n])
random.seed(7)
edge = [10**18, 10**18 - 1, PER - 1, PER, PER + 1, 2**31 - 1, 2**31, 0, 1, 2, 10]
for n in edge + [random.randrange(10**18) for _ in range(400)]:
    got = fib(n)
    assert got == ref(n), (n, got, ref(n))

# throughput benchmark: as many calls as fit in ~0.6 s
ns = [random.randrange(10**18) for _ in range(200000)]
for n in ns[:2000]:
    fib(n)                      # warm up tables/caches
cnt = 0
t0 = time.perf_counter()
while True:
    for n in ns:
        fib(n)
    cnt += len(ns)
    el = time.perf_counter() - t0
    if el > 0.6:
        break
print(int(cnt / el))
