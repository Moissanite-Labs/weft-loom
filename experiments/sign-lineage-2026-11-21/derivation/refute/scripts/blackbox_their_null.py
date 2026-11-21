"""Black-box test of THEIR exact_null.cluster_pvalues / same_position_law against MY brute force.

My checks (exact_refute.py) do not depend on this file. This file loads their module by path
only to feed it inputs and compare outputs with exhaustive enumeration written here.
Run: python3 -I -B blackbox_their_null.py <path to their scripts dir>
"""
import importlib.util
import itertools
import random
import sys
from fractions import Fraction
from math import factorial

spec = importlib.util.spec_from_file_location("their_exact_null", sys.argv[1] + "/exact_null.py")
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

bad = 0
rng = random.Random(4242)
n = 0
for trial in range(300):
    J = rng.randint(1, 6)
    k = rng.randint(1, 14)
    matches = [rng.randrange(J) for _ in range(k)]
    signs = [rng.choice((1, -1)) for _ in range(k)]
    used = sorted(set(matches))
    obs = sum(1 for c in signs if c > 0)
    up = lo = two = 0
    for e in itertools.product((1, -1), repeat=len(used)):
        ee = dict(zip(used, e))
        npl = sum(1 for j, c in zip(matches, signs) if c * ee[j] > 0)
        up += npl >= obs
        lo += npl <= obs
        two += abs(2 * npl - k) >= abs(2 * obs - k)
    den = 2 ** len(used)
    r = T.cluster_pvalues(matches, signs)
    ok = (r["p_upper"] == Fraction(up, den) and r["p_lower"] == Fraction(lo, den) and r["p_two"] == Fraction(two, den))
    bad += not ok
    n += 1
print("cluster_pvalues vs brute force:", n - bad, "/", n, "agree")

# zero sign input: their routine requires +1/-1 (a corr of exactly 0 must be handled upstream)
try:
    T.cluster_pvalues([0, 0], [1, 0])
    print("zero sign accepted")
except Exception as exc:
    print("zero sign rejected:", type(exc).__name__)

# same_position_law vs brute force over permutations with explicit disjoint position sets
bad = 0
for trial in range(40):
    N = rng.randint(2, 7)
    pos = list(range(N))
    rng.shuffle(pos)
    nm = rng.randint(1, N)
    J = rng.randint(1, nm)
    sets = [[] for _ in range(J)]
    for p in pos[:nm]:
        sets[rng.randrange(J)].append(p)
    sets = [s for s in sets if s]
    law = {}
    for pi in itertools.permutations(range(N)):
        F = sum(1 for j, S in enumerate(sets) if pi[j] in S)
        law[F] = law.get(F, 0) + Fraction(1, factorial(N))
    theirs = T.same_position_law([len(s) for s in sets], N)
    ok = all(law.get(k, 0) == (theirs[k] if k < len(theirs) else 0) for k in range(N + 1))
    bad += not ok
print("same_position_law vs brute force:", 40 - bad, "/ 40 agree")
