import sys, importlib, random
import primes_odd
ref = primes_odd.count_primes
random.seed(1)
extra = [random.randrange(5000, 3000000) for _ in range(40)] + [510510*k+d for k in (1,2,3) for d in range(-3,35)] + [20000000, 21234567]
refs = {n: ref(n) for n in list(range(5000)) + extra}
known = {5000000: 348513, 30000000: 1857859, 100000000: 5761455}
for name in sys.argv[1:]:
    f = importlib.import_module(name).count_primes
    bad = [n for n, v in refs.items() if f(n) != v]
    bad += [n for n, v in known.items() if f(n) != v]
    print(name, "OK" if not bad else ("BAD", bad[:10]))
