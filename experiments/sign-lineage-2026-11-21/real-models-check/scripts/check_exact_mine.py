"""Brute-force checks of exact.py (all sign vectors, all relabellings). No bare assert; exit 1 on any failure.
Run under python3 -I -B, -I -O -B and -I -B -W error; output must be byte-identical.
"""
import sys, os, itertools, random
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exact  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def brute_binom(m, k):
    le = ge = 0
    for bits in range(1 << m):
        c = bin(bits).count("1")
        le += c <= k
        ge += c >= k
    return Fraction(le, 1 << m), Fraction(ge, 1 << m)


def brute_cluster(vals, s):
    le = ge = 0
    n = len(vals)
    for bits in range(1 << n):
        t = sum(v if (bits >> i) & 1 else -v for i, v in enumerate(vals))
        le += t <= s
        ge += t >= s
    return Fraction(le, 1 << n), Fraction(ge, 1 << n)


def brute_same(layers_sets):
    """layers_sets: list of (N, list of disjoint sets S_j indexed by target j). Law of F over independent perms."""
    dist = {0: Fraction(1)}
    for N, S in layers_sets:
        cnt = {}
        tot = 0
        for p in itertools.permutations(range(N)):
            f = sum(1 for j in range(N) if p[j] in S[j])
            cnt[f] = cnt.get(f, 0) + 1
            tot += 1
        new = {}
        for a, x in dist.items():
            for b, y in cnt.items():
                new[a + b] = new.get(a + b, 0) + x * Fraction(y, tot)
        dist = new
    return dist


ncase = {"binom": 0, "cluster": 0, "same_exact": 0, "same_bracket": 0, "mean_var": 0}
for m in range(0, 13):
    for k in range(-1, m + 2):
        lo, up = exact.binom_tails(m, k)
        blo, bup = brute_binom(m, k)
        check(lo == blo and up == bup, "binom %d %d" % (m, k))
        ncase["binom"] += 1

rng = random.Random(20261121)
for t in range(200):
    n = rng.randint(1, 9)
    vals = [rng.choice([1, 1, 1, 2, 3, 5]) for _ in range(n)]
    hist = {}
    for v in vals:
        hist[v] = hist.get(v, 0) + 1
    tot = sum(vals)
    for s in range(-tot - 1, tot + 2):
        a = exact.cluster_tails(hist, s)
        b = brute_cluster(vals, s)
        check(a == b, "cluster %s %d" % (vals, s))
        ncase["cluster"] += 1


def random_layer(N, hA):
    # assign each of hA source positions to a random target (some targets empty); S_j disjoint
    S = [set() for _ in range(N)]
    for i in range(hA):
        if rng.random() < 0.8:
            S[rng.randrange(N)].add(i)
    return S


for t in range(120):
    nl = rng.choice([1, 1, 2])
    layers_sets = []
    for _ in range(nl):
        N = rng.randint(2, 6)
        hA = rng.randint(1, N)
        layers_sets.append((N, random_layer(N, hA)))
    law = brute_same(layers_sets)
    layers = []
    for N, S in layers_sets:
        h = {}
        for s in S:
            if len(s):
                h[len(s)] = h.get(len(s), 0) + 1
        layers.append((N, h))
    mean = sum(k * p for k, p in law.items())
    var = sum(k * k * p for k, p in law.items()) - mean * mean
    check(exact.same_pos_mean(layers) == mean, "same mean %s" % layers)
    check(exact.same_pos_variance(layers) == var, "same var %s" % layers)
    ncase["mean_var"] += 1
    for k in range(0, 8):
        true = sum((p for f, p in law.items() if f >= k), Fraction(0))
        lo, hi = exact.same_pos_upper(layers, k, extra=80)
        check(lo == true and hi == true, "same exact %s k=%d" % (layers, k))
        ncase["same_exact"] += 1
        for extra in (0, 1, 2):
            lo, hi = exact.same_pos_upper(layers, k, extra=extra)
            check(lo <= true <= hi, "same bracket %s k=%d extra=%d" % (layers, k, extra))
            ncase["same_bracket"] += 1

# must-fail controls
ctrl1 = exact.cluster_tails({1: 2, 3: 1}, 1) == brute_cluster([1, 1, 2], 1)
ctrl2 = exact.same_pos_upper([(4, {1: 2})], 1) == exact.same_pos_upper([(5, {1: 2})], 1)
check(not ctrl1, "control: wrong cluster values not caught")
check(not ctrl2, "control: wrong layer width not caught")
# refuter's 3-to-1 example: signs (+,+,-) to one target: |s| = 1, law {1:1/2, 2:1/2} for N+, not Bin(3,1/2)
lo, up = exact.cluster_tails({1: 1}, 1)
check(up == Fraction(1, 2), "refuter 3-to-1 example")

print("cases", " ".join("%s=%d" % kv for kv in sorted(ncase.items())))
print("controls caught", int(not ctrl1) + int(not ctrl2), "of 2")
print("failures", len(fails))
for f in fails[:20]:
    print("FAIL", f)
sys.exit(1 if fails else 0)
