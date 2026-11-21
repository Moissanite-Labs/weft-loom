"""Advocate pass: N1, the sibling's Z2 chance-agreement algebra, checked exactly.

1. Identity A = p1 p2 + (1-p1)(1-p2) = 1/2 + (1/2)(2p1-1)(2p2-1) on a rational grid.
2. With p1 = 1, A = p2 for every p2: the 83-87% band is matched by any p2 in [83/100, 87/100]
   (a one-parameter fit, not a prediction).
3. If either side has p = 1/2 (a free sign gauge), A = 1/2 whatever the other side.
4. Gauge fact on a toy gated MLP in exact rationals: flipping up-row j and down-column j leaves
   the output unchanged; the same flip in an ungated MLP with a non-odd activation does not.
5. Kappa for the Qwen pairs at p = 1/2 equals 2A - 1.
No bare assert. Exit 1 on any failure.
"""
import random
import sys
from fractions import Fraction as F

FAIL = []


def chk(cond, msg):
    if not cond:
        FAIL.append(msg)
        print("FAIL:", msg)


def act(x):
    # a rational, non-odd activation (ReLU-squared-like), enough for the gauge check
    return x * x if x > 0 else F(0)


def main():
    grid = [F(k, 20) for k in range(21)]
    for p1 in grid:
        for p2 in grid:
            a = p1 * p2 + (1 - p1) * (1 - p2)
            chk(a == F(1, 2) + F(1, 2) * (2 * p1 - 1) * (2 * p2 - 1), "identity at %s,%s" % (p1, p2))
            if p1 == 1:
                chk(a == p2, "p1=1 gives A=p2")
            if p1 == F(1, 2) or p2 == F(1, 2):
                chk(a == F(1, 2), "free gauge gives 1/2")
    band = [p for p in (F(k, 100) for k in range(0, 101)) if F(83, 100) <= p <= F(87, 100)]
    print("p1 = 1: A_chance = p2 exactly; p2 values on a 1/100 grid reproducing 83-87%%: %d (%s..%s)" % (
        len(band), band[0], band[-1]))
    print("one side with p = 1/2: A_chance = 1/2 for every p of the other side (checked on the grid)")
    for name, a in (("Qwen3.5 0.8B/2B", F(93, 100)), ("Qwen3.5 4B/9B", F(98, 100)), ("Qwen3 0.6B/1.7B", F(88, 100))):
        kappa = (a - F(1, 2)) / (1 - F(1, 2))
        chk(kappa == 2 * a - 1, "kappa")
        print("%s: A = %s, kappa at p = 1/2 = %s" % (name, a, kappa))

    rng = random.Random(31337)
    d_in, d_ff, d_out = 3, 4, 2

    def rnd():
        return F(rng.randint(-9, 9), rng.randint(1, 7))

    G = [[rnd() for _ in range(d_in)] for _ in range(d_ff)]
    U = [[rnd() for _ in range(d_in)] for _ in range(d_ff)]
    D = [[rnd() for _ in range(d_ff)] for _ in range(d_out)]
    xs = [[rnd() for _ in range(d_in)] for _ in range(6)]

    def dot(a, b):
        return sum(p * q for p, q in zip(a, b))

    def gated(G, U, D, x):
        h = [act(dot(G[j], x)) * dot(U[j], x) for j in range(d_ff)]
        return [dot(D[i], h) for i in range(d_out)]

    def plain(U, D, x):
        h = [act(dot(U[j], x)) for j in range(d_ff)]
        return [dot(D[i], h) for i in range(d_out)]

    j = 1
    U2 = [row[:] for row in U]
    U2[j] = [-v for v in U2[j]]
    D2 = [row[:] for row in D]
    for i in range(d_out):
        D2[i][j] = -D2[i][j]
    same_g = all(gated(G, U, D, x) == gated(G, U2, D2, x) for x in xs)
    same_p = all(plain(U, D, x) == plain(U2, D2, x) for x in xs)
    print("gated MLP, flip up-row and down-column %d: outputs identical on 6 inputs: %s" % (j, same_g))
    print("ungated MLP, same flip: outputs identical: %s (must be False)" % same_p)
    chk(same_g, "gauge holds for gated")
    chk(not same_p, "control: ungated flip must change output")
    if FAIL:
        return 1
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
