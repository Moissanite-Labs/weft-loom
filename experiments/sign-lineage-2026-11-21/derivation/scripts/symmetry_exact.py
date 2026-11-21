"""Exact checks for Statements S1 (symmetry), S2 (equivariance of training steps)
and S3b (joint sign flips give an exact binomial law).

Rational arithmetic (fractions.Fraction) plus one sympy identity with a generic,
undefined activation function. No floats. No bare assert.
Run: python3 -I -B symmetry_exact.py  (also -I -O -B and -I -B -W error)
"""
import itertools
import json
import sys
from fractions import Fraction
from math import comb

import sympy


class CheckFailure(Exception):
    pass


def require(cond, msg):
    if not cond:
        raise CheckFailure(msg)


def rng(seed):
    x = seed
    while True:
        x = (6364136223846793005 * x + 1442695040888963407) % (2 ** 64)
        yield x >> 33


def rat(g):
    return Fraction(int(next(g) % 15) - 7, 1 + int(next(g) % 4))


# exact activations: any act works for the gated identity; these are computable in Q
def relu(z):
    return z if z > 0 else Fraction(0)


def relu_d(z):
    return Fraction(1) if z > 0 else Fraction(0)


def rsilu(z):  # rational SiLU-like surrogate, not odd
    return z * (1 + z / (1 + abs(z))) / 2


def rodd(z):  # odd rational squashing function
    return z / (1 + abs(z))


def matvec(M, x):
    return [sum((a * b for a, b in zip(row, x)), Fraction(0)) for row in M]


def gated(G, U, D, x, act):
    g = matvec(G, x)
    u = matvec(U, x)
    hid = [act(a) * b for a, b in zip(g, u)]
    return matvec(D, hid), hid


def plain(U, D, x, act):
    hid = [act(a) for a in matvec(U, x)]
    return matvec(D, hid), hid


def flip_row(M, i):
    return [[-v for v in row] if k == i else list(row) for k, row in enumerate(M)]


def flip_col(M, i):
    return [[-v if k == i else v for k, v in enumerate(row)] for row in M]


def perm_rows(M, p):
    return [list(M[p[k]]) for k in range(len(p))]


def perm_cols(M, p):
    return [[row[p[k]] for k in range(len(p))] for row in M]


def s1_identity():
    g = rng(11)
    d, h = 3, 4
    G = [[rat(g) for _ in range(d)] for _ in range(h)]
    U = [[rat(g) for _ in range(d)] for _ in range(h)]
    D = [[rat(g) for _ in range(h)] for _ in range(d)]
    X = [[rat(g) for _ in range(d)] for _ in range(6)]
    out = {}
    for name, act in (("relu", relu), ("rsilu", rsilu), ("rodd", rodd)):
        for i in range(h):
            for x in X:
                y0, h0 = gated(G, U, D, x, act)
                y1, h1 = gated(G, flip_row(U, i), flip_col(D, i), x, act)
                require(y0 == y1, "S1 gated flip changed output (%s, unit %d)" % (name, i))
                require(h1[i] == -h0[i] and all(h1[k] == h0[k] for k in range(h) if k != i),
                        "S1 hidden trace of unit %d did not flip exactly" % i)
        for p in itertools.permutations(range(h)):
            for x in X:
                y0, h0 = gated(G, U, D, x, act)
                y1, h1 = gated(perm_rows(G, p), perm_rows(U, p), perm_cols(D, p), x, act)
                require(y0 == y1, "S1 permutation changed output")
                require(h1 == [h0[p[k]] for k in range(h)], "S1 permuted trace mismatch")
        out["gated_flip_and_perm_" + name] = "pass: %d flips x %d inputs, 24 permutations" % (h, len(X))
    # must-fail controls
    ctrl = {}
    ctrl["flip_U_only"] = any(gated(G, flip_row(U, i), D, x, rsilu)[0] != gated(G, U, D, x, rsilu)[0]
                              for i in range(h) for x in X)
    ctrl["flip_G_and_D_nonodd_act"] = any(
        gated(flip_row(G, i), U, flip_col(D, i), x, rsilu)[0] != gated(G, U, D, x, rsilu)[0]
        for i in range(h) for x in X)
    ctrl["plain_relu_flip_U_and_D"] = any(
        plain(flip_row(U, i), flip_col(D, i), x, relu)[0] != plain(U, D, x, relu)[0]
        for i in range(h) for x in X)
    ctrl["plain_gelu_like_flip_U_and_D"] = any(
        plain(flip_row(U, i), flip_col(D, i), x, rsilu)[0] != plain(U, D, x, rsilu)[0]
        for i in range(h) for x in X)
    for k, v in ctrl.items():
        require(v, "must-fail control %s did NOT change the output" % k)
    out["controls_changed_output_as_required"] = sorted(ctrl)
    # positive control: plain block with an odd activation keeps the sign symmetry
    for i in range(h):
        for x in X:
            require(plain(flip_row(U, i), flip_col(D, i), x, rodd)[0] == plain(U, D, x, rodd)[0],
                    "plain odd-activation block lost its sign symmetry")
    out["plain_odd_activation_keeps_symmetry"] = "pass"
    return out


def s1_symbolic():
    act = sympy.Function("act")
    x = sympy.symbols("x0:2")
    G = sympy.Matrix(2, 2, sympy.symbols("g0:4"))
    U = sympy.Matrix(2, 2, sympy.symbols("u0:4"))
    D = sympy.Matrix(2, 2, sympy.symbols("d0:4"))
    xv = sympy.Matrix(x)

    def y(G, U, D):
        gx, ux = G * xv, U * xv
        hid = sympy.Matrix([act(gx[k]) * ux[k] for k in range(2)])
        return D * hid

    F = sympy.diag(-1, 1)
    diff = sympy.expand(y(G, F * U, D * F) - y(G, U, D))
    require(diff == sympy.zeros(2, 1), "symbolic gated identity failed")
    ctrl = sympy.expand(y(G, F * U, D) - y(G, U, D))
    require(ctrl != sympy.zeros(2, 1), "symbolic control (flip U only) did not fail")
    return {"symbolic_generic_act": "pass: D F (act(G x) * (F U x)) == D (act(G x) * (U x)), F=diag(-1,1)",
            "symbolic_control_flip_U_only": "nonzero difference, as required"}


# ------------------------------------------------------------------ S2: training steps

def loss_and_grad(theta, data, penalty=Fraction(0)):
    """Squared loss of the ReLU-gated block, exact gradient by hand.
    penalty adds penalty * sum_x sum_i hid_i(x): a sign-tying term (control)."""
    G, U, D = theta
    h, d, dout = len(G), len(G[0]), len(D)
    dG = [[Fraction(0)] * d for _ in range(h)]
    dU = [[Fraction(0)] * d for _ in range(h)]
    dD = [[Fraction(0)] * h for _ in range(dout)]
    L = Fraction(0)
    for x, t in data:
        gx = matvec(G, x)
        ux = matvec(U, x)
        a = [relu(v) for v in gx]
        hid = [ai * ui for ai, ui in zip(a, ux)]
        y = matvec(D, hid)
        r = [yi - ti for yi, ti in zip(y, t)]
        L += sum(v * v for v in r) / 2 + penalty * sum(hid)
        for o in range(dout):
            for k in range(h):
                dD[o][k] += r[o] * hid[k]
        dhid = [sum(D[o][k] * r[o] for o in range(dout)) + penalty for k in range(h)]
        for k in range(h):
            du = dhid[k] * a[k]
            dg = dhid[k] * ux[k] * relu_d(gx[k])
            for c in range(d):
                dU[k][c] += du * x[c]
                dG[k][c] += dg * x[c]
    return L, (dG, dU, dD)


def act_T(theta, i, p):
    """Group element: flip unit i (U row, D column), then permute units by p."""
    G, U, D = theta
    U2, D2 = flip_row(U, i), flip_col(D, i)
    return (perm_rows(G, p), perm_rows(U2, p), perm_cols(D2, p))


def act_absT(theta, p):
    G, U, D = theta
    return (perm_rows(G, p), perm_rows(U, p), perm_cols(D, p))


def axpy(a, X, Y):
    return tuple([[a * x + y for x, y in zip(rx, ry)] for rx, ry in zip(MX, MY)] for MX, MY in zip(X, Y))


def sq(X):
    return tuple([[x * x for x in r] for r in M] for M in X)


def scal(a, X):
    return tuple([[a * x for x in r] for r in M] for M in X)


def norm2(X):
    return sum((x * x for M in X for r in M for x in r), Fraction(0))


def s2_equivariance():
    g = rng(23)
    d, h, dout = 2, 3, 2
    G = [[rat(g) for _ in range(d)] for _ in range(h)]
    U = [[rat(g) for _ in range(d)] for _ in range(h)]
    D = [[rat(g) for _ in range(h)] for _ in range(dout)]
    data = [([rat(g) for _ in range(d)], [rat(g) for _ in range(dout)]) for _ in range(4)]
    theta = (G, U, D)
    i, p = 1, (2, 0, 1)
    out = {}
    L0, gr0 = loss_and_grad(theta, data)
    L1, gr1 = loss_and_grad(act_T(theta, i, p), data)
    require(L0 == L1, "S2 loss not invariant")
    require(gr1 == act_T(gr0, i, p), "S2 gradient not equivariant")
    out["loss_invariant_gradient_equivariant"] = "pass"
    # GD, heavy-ball momentum, Adam moments, decoupled weight decay, global-norm clip: 3 steps
    eta, beta, b1, b2, lam = Fraction(1, 10), Fraction(9, 10), Fraction(9, 10), Fraction(99, 100), Fraction(1, 100)
    th_a, th_b = theta, act_T(theta, i, p)
    mom_a = mom_b = scal(0, theta)
    m_a = m_b = v_a = v_b = scal(0, theta)
    for step in range(3):
        _, ga = loss_and_grad(th_a, data)
        _, gb = loss_and_grad(th_b, data)
        require(norm2(ga) == norm2(gb), "global grad norm differs: clipping factor would differ")
        mom_a = axpy(beta, mom_a, ga)
        mom_b = axpy(beta, mom_b, gb)
        m_a = axpy(b1, m_a, scal(1 - b1, ga))
        m_b = axpy(b1, m_b, scal(1 - b1, gb))
        v_a = axpy(b2, v_a, scal(1 - b2, sq(ga)))
        v_b = axpy(b2, v_b, scal(1 - b2, sq(gb)))
        require(mom_b == act_T(mom_a, i, p), "momentum state not equivariant")
        require(m_b == act_T(m_a, i, p), "Adam first moment not equivariant (T m)")
        require(v_b == act_absT(v_a, p), "Adam second moment not |T|-equivariant")
        # parameter update: decoupled weight decay + momentum step (rational path)
        th_a = axpy(-eta, mom_a, scal(1 - eta * lam, th_a))
        th_b = axpy(-eta, mom_b, scal(1 - eta * lam, th_b))
        require(th_b == act_T(th_a, i, p), "parameters after step %d not equivariant" % step)
    out["three_steps_momentum_adam_moments_weight_decay"] = "pass"
    # control: a sign-tying penalty (sum of hidden activations) must break equivariance
    _, gp0 = loss_and_grad(theta, data, penalty=Fraction(1, 3))
    _, gp1 = loss_and_grad(act_T(theta, i, p), data, penalty=Fraction(1, 3))
    require(gp1 != act_T(gp0, i, p), "control: sign-tying penalty did not break equivariance")
    out["control_sign_tying_penalty_breaks_equivariance"] = "pass (broken, as required)"
    return out


# ------------------------------------------------------------------ S3b: joint flips

def s3b_joint_flip_binomial():
    g = rng(99)
    out = {"cases": 0}
    for trial in range(12):
        nA = 2 + next(g) % 6
        nB = 1 + next(g) % 4
        match = [next(g) % nB for _ in range(nA)]
        c = [1 if next(g) % 2 else -1 for _ in range(nA)]
        counts = [0] * (nA + 1)
        for delta in itertools.product((1, -1), repeat=nA):
            for eps in itertools.product((1, -1), repeat=nB):
                n = sum(1 for k in range(nA) if delta[k] * eps[match[k]] * c[k] == 1)
                counts[n] += 1
        tot = 2 ** (nA + nB)
        require([Fraction(x, tot) for x in counts] == [Fraction(comb(nA, k), 2 ** nA) for k in range(nA + 1)],
                "S3b joint-flip law is not binomial")
        out["cases"] += 1
    # conditional on A (only eps random), a same-sign cluster is not binomial
    match, c = [0, 0, 0, 1], [1, 1, 1, 1]
    counts = [0] * 5
    for eps in itertools.product((1, -1), repeat=2):
        counts[sum(1 for k in range(4) if eps[match[k]] * c[k] == 1)] += 1
    require(counts != [1, 4, 6, 4, 1], "control: conditional law unexpectedly binomial")
    out["conditional_on_A_cluster_example_law_x4"] = counts
    return out


def main():
    res = {"S1": s1_identity(), "S1_symbolic": s1_symbolic(), "S2": s2_equivariance(),
           "S3b": s3b_joint_flip_binomial()}
    print(json.dumps(res, sort_keys=True, indent=1))


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as e:
        print("CHECK FAILED:", e)
        sys.exit(1)
