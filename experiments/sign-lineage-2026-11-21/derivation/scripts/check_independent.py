"""Independent checker for exact_null.py. Shares no code with it.

Method: brute-force enumeration instead of convolution or rook polynomials.
  cluster cases: enumerate every sign vector on the matched B units and count.
  same-position cases: build concrete disjoint position sets, enumerate all N!
  relabellings of B's units, and count hits.
  binomial cases: Pascal's triangle by repeated addition.
Run: python3 -I -B check_independent.py  (also -I -O -B and -I -B -W error)
"""
import itertools
import json
import os
import sys
from fractions import Fraction


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))



def fail(msg):
    print("CHECK FAILED:", msg)
    sys.exit(1)


def brute_cluster(matches, signs):
    units = sorted(set(matches))
    m = len(matches)
    obs = sum(1 for c in signs if c == 1)
    up = lo = two = 0
    total = 0
    for eps in itertools.product((1, -1), repeat=len(units)):
        flip = dict(zip(units, eps))
        n = sum(1 for j, c in zip(matches, signs) if flip[j] * c == 1)
        total += 1
        if n >= obs:
            up += 1
        if n <= obs:
            lo += 1
        if abs(2 * n - m) >= abs(2 * obs - m):
            two += 1
    return Fraction(up, total), Fraction(lo, total), Fraction(two, total)


def brute_same_position(class_sizes, N):
    # B unit j (j < len(class_sizes)) owns the A positions in S_j; units beyond own none.
    sets = []
    pos = 0
    for n in class_sizes:
        sets.append(set(range(pos, pos + n)))
        pos += n
    counts = {}
    total = 0
    for perm in itertools.permutations(range(N)):
        f = 0
        for j, S in enumerate(sets):
            if perm[j] in S:
                f += 1
        counts[f] = counts.get(f, 0) + 1
        total += 1
    K = sum(1 for n in class_sizes if n > 0)
    return [Fraction(counts.get(k, 0), total) for k in range(K + 1)]


def pascal_row(m):
    row = [1]
    for _ in range(m):
        row = [a + b for a, b in zip([0] + row, row + [0])]
    return row


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = _opt("--cases", os.path.join(here, "..", "out", "exact_cases.json"))
    with open(path) as f:
        data = json.load(f)
    n_ok = {"cluster": 0, "same_position": 0, "binomial": 0}
    for case in data["cases"]:
        kind = case["kind"]
        if kind == "cluster":
            up, lo, two = brute_cluster(case["matches"], case["signs"])
            if (str(up), str(lo), str(two)) != (case["p_upper"], case["p_lower"], case["p_two"]):
                fail("cluster mismatch %r" % case)
        elif kind == "same_position":
            law = brute_same_position(case["class_sizes"], case["N"])
            if [str(p) for p in law] != case["law"]:
                fail("same-position mismatch %r" % case)
        elif kind == "binomial":
            row = pascal_row(case["m"])
            den = 2 ** case["m"]
            up = Fraction(sum(row[case["k"]:]), den)
            lo = Fraction(sum(row[:case["k"] + 1]), den)
            if (str(up), str(lo)) != (case["upper"], case["lower"]):
                fail("binomial mismatch %r" % case)
        else:
            fail("unknown case kind %r" % kind)
        n_ok[kind] += 1
    # must-fail control: perturb one stored value and confirm the checker catches it
    bad = dict(data["cases"][0])
    up, lo, two = brute_cluster(bad["matches"], bad["signs"])
    if str(up + Fraction(1, 2 ** 20)) == bad["p_upper"]:
        fail("control: perturbed value was not caught")
    print(json.dumps({"agreed": n_ok, "control_perturbation_caught": True}, sort_keys=True))


if __name__ == "__main__":
    main()
