import sys, time, random, importlib
sys.path.insert(0, '..')
from bench import ref, M
rnd = random.Random(7)
tests = list(range(3000)) + [10**18, 10**18-1, 2**59, 2**60-1, 1000000008, 1000000007, 500000004, 500000005, 2000000016, 2000000015] + [rnd.randrange(10**18+1) for _ in range(3000)] + [rnd.randrange(3*10**9) for _ in range(2000)]
ns = [rnd.randrange(10**17, 10**18 + 1) for _ in range(5000)]
for name in ['cur', 'a', 'b', 'c', 'd']:
    f = importlib.import_module(name).fib
    bad = [n for n in tests if f(n) != ref(n)]
    best = 9e9
    for _ in range(15):
        t = time.process_time()
        for n in ns: f(n)
        best = min(best, time.process_time() - t)
    print(name, 'BAD %d e.g. %s' % (len(bad), bad[:3]) if bad else 'ok', '%.0f/s' % (len(ns) / best))
