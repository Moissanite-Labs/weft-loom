import time, random, importlib, subprocess, sys
from bench import ref
rnd = random.Random(7)
tests = list(range(5000)) + [10**18, 10**18-1, 2**59, 2**60-1, 1000000008, 1000000007, 1000000009, 500000003, 500000004, 500000005, 500000006, 2000000016, 2000000015, 2000000017, 1500000012,1500000011,1500000013] + [rnd.randrange(10**18+1) for _ in range(3000)] + [rnd.randrange(5*10**9) for _ in range(3000)]
refs = [ref(n) for n in tests]
ns = [rnd.randrange(10**17, 10**18 + 1) for _ in range(5000)]
for name in ['fibmod', 'w1', 'w2', 'w3', 'w4']:
    t0 = time.perf_counter(); f = importlib.import_module(name).fib; imp = time.perf_counter() - t0
    ok = all(f(n) == r for n, r in zip(tests, refs))
    best = 1e9
    for _ in range(15):
        t = time.process_time()
        for n in ns: f(n)
        best = min(best, time.process_time() - t)
    cli = subprocess.run([sys.executable, name + '.py', '10'], capture_output=True, text=True).stdout.strip()
    print(name, 'ok' if ok else 'WRONG', 'calls/s %.0f' % (len(ns)/best), 'import_ms %.3f' % (imp*1e3), 'cli', cli)
