#!/usr/bin/env python3
"""Generate differential cases. All numerics are float32-exact (what C can represent)
except class 'f64only_*' which Python/JS get as float64 and C cannot represent."""
import json, math, random, struct, sys
import numpy as np

rng = random.Random(20261115)
nrng = np.random.default_rng(20261115)
INF = float("inf")
def f32(x): return struct.unpack("<f", struct.pack("<f", x))[0] if abs(x) < 3.5e38 or not math.isfinite(x) else (INF if x > 0 else -INF)
def bits(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def enc(x):
    if x != x: return "NaN"
    if x == INF: return "Inf"
    if x == -INF: return "-Inf"
    return repr(float(x))
def nextup(x): return float(np.nextafter(np.float32(x), np.float32(INF)))
def nextdn(x): return float(np.nextafter(np.float32(x), np.float32(-INF)))

cases = []
def _r(x): return f32(x) if math.isfinite(x) else x
def add(cls, base, cand, r, b, c, mask=None, c_ok=True):
    if c_ok:
        base = [_r(x) for x in base]; cand = [_r(x) for x in cand]; r = _r(r); b = _r(b); c = _r(c)
    cases.append(dict(cls=cls, base=list(base), cand=list(cand), r=r, b=b, c=c, mask=mask, c_ok=c_ok))

def vec(n, scale=1.0):
    return [f32(rng.gauss(0, scale)) for _ in range(n)]

def dist64(b, c):
    return math.sqrt(math.fsum((x - y) ** 2 for x, y in zip(b, c)))

# 1 random typical, around radius
for _ in range(4000):
    n = rng.choice([1, 2, 3, 8, 16, 64])
    b = vec(n, 10 ** rng.uniform(-3, 3)); c = [f32(x + rng.gauss(0, 10 ** rng.uniform(-3, 2))) for x in b]
    d = dist64(b, c)
    r = f32(d * rng.choice([0.5, 0.999, 1.0, 1.001, 2.0]))
    bud = f32(10 ** rng.uniform(-2, 4)); cost = f32(bud * rng.choice([0.01, 0.5, 1.0, 1.0, 0.999]))
    add("random_near_radius", b, c, r, bud, cost)
# 2 distance exactly at radius (exact arithmetic)
for _ in range(1500):
    k = rng.choice([(3,4,5),(5,12,13),(8,15,17),(1,0,1),(0,0,0),(6,8,10),(0.5,1.2,1.3)])
    b = [f32(rng.choice([0, 1, -2.5, 100]))]*2
    c = [f32(b[0]+k[0]), f32(b[1]+k[1])]
    r = f32(k[2]); mode = rng.choice(["eq","up","dn"])
    if mode == "up": r = nextup(r)
    if mode == "dn": r = nextdn(r)
    add("dist_exactly_at_radius_"+mode, b, c, r, 10.0, 1.0)
# 3 cost == budget, and neighbours
for _ in range(1500):
    bud = f32(10 ** rng.uniform(-30, 30)); mode = rng.choice(["eq","dn","up"])
    cost = bud if mode=="eq" else (nextdn(bud) if mode=="dn" else nextup(bud))
    add("cost_eq_budget_"+mode, [0.0, 0.0], [f32(0.1), 0.0], 1.0, bud, cost)
# 4 budget/cost sign classes
specials = [0.0, -0.0, 1.0, -1.0, 1e-45, -1e-45, 1.17549435e-38, 3.4028234e38, -3.4028234e38, INF, -INF, float("nan"), 0.5, 100.0]
for b_ in specials:
    for c_ in specials:
        for r_ in [0.0, 1.0, -1.0, INF, float("nan"), 1e-45, 3.4028234e38]:
            add("param_grid", [0.0, 0.0], [0.5, 0.0], f32(r_) if math.isfinite(r_) else r_, f32(b_) if math.isfinite(b_) else b_, f32(c_) if math.isfinite(c_) else c_)
# 5 non-finite weights, in baseline/cand, various positions
for _ in range(1500):
    n = rng.choice([1, 3, 8]); b = vec(n); c = vec(n)
    bad = rng.choice([float("nan"), INF, -INF]); where = rng.choice(["b", "c", "both"])
    i = rng.randrange(n)
    if where in ("b", "both"): b[i] = bad
    if where in ("c", "both"): c[i] = bad
    # budget possibly problematic too, to test precedence
    bud = rng.choice([10.0, 10.0, 0.0, -5.0, 1.0]); cost = rng.choice([1.0, 1.0, 0.0, -1.0, 5.0, 20.0]); r = rng.choice([100.0, 1.0, -1.0])
    add("nonfinite_weights_precedence", b, c, r, bud, cost)
# 6 radius tiny/huge/negative/zero
for _ in range(1200):
    n = rng.choice([1, 4]); b = vec(n); same = rng.random() < 0.4
    c = list(b) if same else [f32(x + 1e-6) for x in b]
    r = rng.choice([0.0, -0.0, 1e-45, 1e-38, 1e-30, 3.4028234e38, -1e-45, -1.0, 1e20])
    add("radius_extremes_"+("same" if same else "moved"), b, c, r, 10.0, 1.0)
# 7 huge weights / overflow
for _ in range(1500):
    n = rng.choice([1, 2, 4])
    mag = rng.choice([1e20, 1e25, 1e30, 1e35, 3.0e38, 3.4028234e38])
    b = [f32(rng.choice([-1, 1]) * mag * rng.random()) for _ in range(n)]
    c = [f32(rng.choice([-1, 1]) * mag * rng.random()) for _ in range(n)]
    r = f32(rng.choice([1e30, 1e38, 3.4028234e38, INF, 1e10]))
    add("huge_weights", b, c, r, 10.0, 1.0)
# 7b float32-overflow diff (b=-big, c=+big) with huge r
for _ in range(300):
    m = f32(rng.choice([3.4e38, 3.0e38, 2.0e38]))
    add("huge_diff_overflows_f32", [-m, 0.0], [m, 0.0], f32(3.4028234e38), 10.0, 1.0)
# 8 float32 boundary: integers near 2^24, ulp-just-above radius
for _ in range(1500):
    base = float(rng.choice([2**24, 2**24+2, 2**23, 1.0, 1e7, 3.4e38/2]))
    d = f32(rng.choice([1.0, 2.0, 3.0, 0.1, 1e-3]))
    b = [f32(base)]; c = [f32(base + d)]
    exact = abs(c[0] - b[0])
    r = rng.choice([exact, nextup(exact), nextdn(exact), f32(exact*(1+2**-23)), f32(exact*(1-2**-23))])
    add("f32_boundary", b, c, r, 10.0, 1.0)
# 9 empty arrays
for _ in range(300):
    add("empty_arrays", [], [], rng.choice([1.0, 0.0]), rng.choice([10.0, 0.0, -1.0, INF]), rng.choice([1.0, 0.0, 20.0]))
# 10 mismatched array lengths (C cannot express)
for _ in range(500):
    n = rng.choice([1, 2, 5]); m = n + rng.choice([-1, 1, 2]) if n > 1 else 2
    add("mismatched_lengths", vec(n), vec(m), 100.0, rng.choice([10.0, -1.0, 0.0]), rng.choice([1.0, 20.0, 0.0]), c_ok=False)
# 11 Zeno/tiny cost relative to budget
for _ in range(1500):
    bud = f32(10 ** rng.uniform(0, 12)); cost = f32(bud * 10 ** rng.uniform(-12, -5))
    add("zeno_tiny_cost", [0.0], [0.1], 1.0, bud, cost)
# 12 denormal budget/cost
for _ in range(400):
    add("denormal_budget_cost", [0.0], [0.1], 1.0, rng.choice([1e-45, 2.8e-45, 1e-40, 1.17549435e-38]), rng.choice([1e-45, 1e-40, 1.4e-45, 5.6e-45]))
# 13 masks (Python vs C only)
for _ in range(2500):
    n = rng.choice([2, 4, 8]); b = vec(n); c = [f32(x + rng.gauss(0, 0.1)) for x in b]
    m = [rng.choice([0, 0, 1]) for _ in range(n)]
    mode = rng.choice(["locked_equal", "locked_ulp", "locked_zeros", "locked_free"])
    for i in range(n):
        if m[i]:
            if mode == "locked_equal": c[i] = b[i]
            elif mode == "locked_ulp": c[i] = nextup(b[i]) if rng.random() < 0.5 else b[i]
            elif mode == "locked_zeros": b[i] = rng.choice([0.0, -0.0]); c[i] = rng.choice([0.0, -0.0])
    d = dist64([x if not mm else 0 for x, mm in zip(b, m)], [x if not mm else 0 for x, mm in zip(c, m)])
    add("mask_"+mode, b, c, f32(d*rng.choice([0.99, 1.0, 1.01]) + 1e-3), 10.0, 1.0, mask=m)
# 13b mask length mismatch + mask on empty (C can't express mismatched mask length)
for _ in range(100):
    n = 4; add("mask_length_mismatch", vec(n), vec(n), 10.0, 10.0, 1.0, mask=[0, 1], c_ok=False)
# 14 negative zero weights, equal vectors
for _ in range(500):
    n = rng.choice([1, 3]); b = [rng.choice([0.0, -0.0]) for _ in range(n)]; c = [rng.choice([0.0, -0.0]) for _ in range(n)]
    add("negzero_weights", b, c, rng.choice([0.0, 1.0]), 10.0, 1.0)
# 15 long vectors: accumulation (N drift): 65536 elems with r around the true distance
for _ in range(12):
    n = 65536; b = [0.0]*n; step = f32(0.01*rng.choice([1, 3, 7]))
    c = [step]*n
    d = math.sqrt(n)*step
    r = rng.choice([f32(d), nextup(f32(d)), nextdn(f32(d)), f32(d*(1+1e-7)), f32(d*(1-1e-7))])
    add("long_65536_uniform", b, c, r, 10.0, 1.0)
for _ in range(8):
    n = 4096; b = vec(n); c = [f32(x + rng.gauss(0, 0.01)) for x in b]
    d = dist64(b, c); r = rng.choice([f32(d), nextup(f32(d)), nextdn(f32(d))])
    add("long_4096_random", b, c, r, 10.0, 1.0)
# 16 float64-only values (Python/JS only; C can't take them)
for _ in range(400):
    big = rng.choice([1e154, 1e160, 1e200, 1e300])
    add("f64only_huge_diff", [0.0, 0.0], [big, 0.0], 1e308, 10.0, 1.0, c_ok=False)
for _ in range(200):
    add("f64only_budget_fraction", [0.0], [0.1], 1.0, 1.0 + 2**-40, 1.0, c_ok=False)
for _ in range(200):
    add("f64only_r_just_below_dist", [0.0], [1.0], 1.0 - 2**-40, 10.0, 1.0, c_ok=False)

print("cases", len(cases), file=sys.stderr)
from collections import Counter
print(json.dumps(Counter(c["cls"].split("_")[0] if c["cls"].startswith(("mask","long","f64only")) else c["cls"] for c in cases)), file=sys.stderr)
with open("cases.jsonl", "w") as fj, open("cases_c.txt", "w") as fc:
    for i, c in enumerate(cases):
        fj.write(json.dumps(dict(id=i, cls=c["cls"], base=[enc(x) for x in c["base"]], cand=[enc(x) for x in c["cand"]],
                                 r=enc(c["r"]), b=enc(c["b"]), c=enc(c["c"]), mask=c["mask"], c_ok=c["c_ok"])) + "\n")
        if c["c_ok"]:
            n = len(c["base"])
            fc.write(f'{i} {n} {bits(c["r"])} {bits(c["b"])} {bits(c["c"])} {1 if c["mask"] is not None else 0}\n')
            fc.write(" ".join(str(bits(x)) for x in c["base"]) + "\n")
            fc.write(" ".join(str(bits(x)) for x in c["cand"]) + "\n")
            fc.write((" ".join(str(x) for x in c["mask"]) if c["mask"] is not None else "") + "\n")
