import importlib, random, time, sys
sys.path.insert(0, '..')
from bench import ref
M = 1000000007
rnd = random.Random(7)
tests = list(range(5000)) + [10**18, 10**18-1, 1000000008, 1000000007, 500000004, 500000005, 500000003, 2000000016, 2000000015, 2047, 2048, 2049, 4096] + [rnd.randrange(10**18+1) for _ in range(1500)] + [rnd.randrange(2**rnd.randrange(1, 60)) for _ in range(1500)]
want = [ref(n) for n in tests]
ns = [rnd.randrange(10**17, 10**18+1) for _ in range(5000)]
for name in ['v0', 'v1', 'v2', 'v3', 'v4']:
    f = importlib.import_module(name).fib
    bad = [n for n, w in zip(tests, want) if f(n) != w]
    best = 1e9
    for _ in range(9):
        t = time.process_time()
        for n in ns: f(n)
        best = min(best, time.process_time() - t)
    print(name, 'bad', len(bad), bad[:5], 'rate %.0f' % (len(ns) / best))
