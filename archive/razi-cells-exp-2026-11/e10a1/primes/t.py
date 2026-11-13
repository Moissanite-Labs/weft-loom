import time, random, importlib
old = importlib.import_module('old')
random.seed(1)
ns = list(range(0, 1500)) + [random.randrange(1500, 3000000) for _ in range(150)] + [10010*3, 30031, 30029, 510510, 510511, 1021020, 1200003, 2000003, 3000001]
exp = [old.count_primes(n) for n in ns]
known = {1000000: 78498, 5000000: 348513, 10000000: 664579, 50000000: 3001134}
for name in ['old', 'vA', 'vC', 'vD18', 'vD20', 'vD21', 'vD22']:
    m = importlib.import_module(name)
    bad = [n for n, e in zip(ns, exp) if m.count_primes(n) != e]
    bad += [n for n, e in known.items() if m.count_primes(n) != e]
    ts = []
    for n in (5000000, 10000000, 50000000):
        b = 9
        for _ in range(4):
            t0 = time.perf_counter(); m.count_primes(n); b = min(b, time.perf_counter() - t0)
        ts.append(round(b * 1000, 2))
    print(name, 'bad', bad[:5], 'ms', ts, 'work', round(8*ts[0]+2*ts[1]+ts[2], 1))
