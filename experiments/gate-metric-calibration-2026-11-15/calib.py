#!/usr/bin/env python3
"""Gate-metric calibration study (weft-loom issue 7).

Question: which distance between two weight settings predicts how much the
model's behaviour changes? Four candidates are measured on the E13 organism
(24 -> 96 -> 96 -> 8, GELU, 12,488 weights):

  frob    the Frobenius distance ||w - w0||, which the shipped gate bounds
  fisher  the first-order prediction sqrt(d' G d), G = J'J / (n * d_out),
          J the Jacobian of the outputs with respect to the weights on a set
          of fit probes
  probe   the measured output RMS change on the same fit probes
  cert    a proved upper bound on the output change (THEORY.md, section 3)

The target is the output RMS change on held-out inputs the predictors never
saw. Moves come in classes: random, first-order worst case, gradient steps,
moves invisible to the fit probes, a readout flip, a hidden-unit permutation,
a benign graft, and two adversaries that search inside a ball.

The system under test (organism, task world, training, splice) is imported
from the E13 record. Everything that measures is written here, apart from it:
the forward pass, the Jacobian, the adversaries and the bound.

Usage:
  python3 calib.py --seeds 900 901 --out pilot.json          (pilot seeds)
  python3 calib.py --seeds 0 1 2 3 4 5 6 7 8 9 10 11 --out results.json

Needs NumPy only. Every internal check stops the run with a non-zero exit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
E13_PATH = HERE.parent / "e13-geodesic-shunting-plasmid-2026-11-12" / "e13_geodesic_plasmid.py"

D_IN, M1, M2, D_OUT = 24, 96, 96, 8
SHAPES = [(M1, D_IN), (M1,), (M2, M1), (M2,), (D_OUT, M2), (D_OUT,)]
NAMES = ["W1", "b1", "W2", "b2", "W3", "b3"]
SIZES = [int(np.prod(s)) for s in SHAPES]
P = sum(SIZES)
OFFS = np.concatenate([[0], np.cumsum(SIZES)])
RADII = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]
A_GELU = 1.702
RETENTION_DROP_MAX = 0.025  # the E13 native retention bar

# Seed bases. Every stream is separate and none is used by the E13 record
# (which uses 1000+s, 2000+s, 3000+s, 4000+s, 8000+s and world 20261112).
WORLD0, HOST0, DONOR0, FIT0, HELD0, ATT0, DIR0, PKT0 = (
    51_000_000, 52_000_000, 53_000_000, 54_000_000, 55_000_000, 56_000_000, 57_000_000, 58_000_000)


def fail(msg: str) -> None:
    raise SystemExit("FAIL: " + msg)


def load_e13():
    if not E13_PATH.exists():
        fail(f"E13 record not found at {E13_PATH}")
    spec = importlib.util.spec_from_file_location("e13mod", E13_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e13mod"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Forward pass, Jacobian and gradient, written apart from the E13 code
# ---------------------------------------------------------------------------

def sig(t):
    return 1.0 / (1.0 + np.exp(-np.clip(t, -34.04, 34.04)))


def g(z):
    """The E13 activation: z * sigmoid(1.702 z), with its clip at |z| = 20."""
    return z * sig(A_GELU * z)


def gp(z):
    s = sig(A_GELU * z)
    return s + A_GELU * z * s * (1.0 - s)


def split(vec):
    return [vec[OFFS[i]:OFFS[i + 1]].reshape(SHAPES[i]) for i in range(6)]


def flat_org(org):
    return np.concatenate([np.asarray(getattr(org, n), dtype=np.float64).ravel() for n in NAMES])


def to_org(e13, vec):
    W1, b1, W2, b2, W3, b3 = [a.copy() for a in split(vec)]
    return e13.MultiLayerOrganism(W1, b1, W2, b2, W3, b3)


def forward(vec, X, cache=False):
    W1, b1, W2, b2, W3, b3 = split(vec)
    Z1 = X @ W1.T + b1
    H1 = g(Z1)
    Z2 = H1 @ W2.T + b2
    H2 = g(Z2)
    Y = H2 @ W3.T + b3
    if cache:
        return Z1, H1, Z2, H2, Y
    return Y


def jacobian(vec, X):
    """Rows ordered (sample, output); shape (n * D_OUT, P)."""
    W1, b1, W2, b2, W3, b3 = split(vec)
    Z1, H1, Z2, H2, _ = forward(vec, X, cache=True)
    n = X.shape[0]
    G1, G2 = gp(Z1), gp(Z2)
    J = np.zeros((n, D_OUT, P))
    for c in range(D_OUT):
        DZ2 = W3[c][None, :] * G2                       # (n, M2)
        DZ1 = (DZ2 @ W2) * G1                           # (n, M1)
        J[:, c, OFFS[0]:OFFS[1]] = (DZ1[:, :, None] * X[:, None, :]).reshape(n, -1)
        J[:, c, OFFS[1]:OFFS[2]] = DZ1
        J[:, c, OFFS[2]:OFFS[3]] = (DZ2[:, :, None] * H1[:, None, :]).reshape(n, -1)
        J[:, c, OFFS[3]:OFFS[4]] = DZ2
        blk = np.zeros((n, D_OUT, M2))
        blk[:, c, :] = H2
        J[:, c, OFFS[4]:OFFS[5]] = blk.reshape(n, -1)
        J[:, c, OFFS[5] + c] = 1.0
    return J.reshape(n * D_OUT, P)


def vjp(vec, X, R):
    """Gradient with respect to the weights of sum(R * f(vec, X))."""
    W1, b1, W2, b2, W3, b3 = split(vec)
    Z1, H1, Z2, H2, _ = forward(vec, X, cache=True)
    gW3 = R.T @ H2
    gb3 = R.sum(axis=0)
    DZ2 = (R @ W3) * gp(Z2)
    gW2 = DZ2.T @ H1
    gb2 = DZ2.sum(axis=0)
    DZ1 = (DZ2 @ W2) * gp(Z1)
    gW1 = DZ1.T @ X
    gb1 = DZ1.sum(axis=0)
    return np.concatenate([a.ravel() for a in (gW1, gb1, gW2, gb2, gW3, gb3)])


def rms_change(vec, vec0, X, Y0=None):
    if Y0 is None:
        Y0 = forward(vec0, X)
    return float(np.sqrt(np.mean((forward(vec, X) - Y0) ** 2)))


def r2_e13(vec, X, Y):
    """R2 as the E13 record defines it: 1 - MSE / mean(Y^2)."""
    pred = forward(vec, X)
    return 1.0 - float(np.mean((pred - Y) ** 2)) / (float(np.mean(Y ** 2)) + 1e-12)


def row_basis(J):
    """Orthonormal basis of the row space of J, through the small matrix JJ'.

    Rank is decided on the eigenvalues, so rows that depend on others (as the
    centred logits of the transformer do) are handled.
    """
    ev, U = np.linalg.eigh(J @ J.T)
    keep = ev > 1e-12 * ev.max()
    V = J.T @ (U[:, keep] / np.sqrt(ev[keep]))
    Q, _ = np.linalg.qr(V)
    return Q


def unit(v):
    nrm = float(np.linalg.norm(v))
    if not (nrm > 0.0 and math.isfinite(nrm)):
        fail("direction with zero or non-finite norm")
    return v / nrm


# ---------------------------------------------------------------------------
# The proved bound (THEORY.md section 3)
# ---------------------------------------------------------------------------

def gelu_slope_bound():
    """Upper bound on sup |g'| over the reals.

    On [-20, 20] by subdivision: |g''| <= 1.5 there (THEORY.md, section 3), so
    the largest grid value plus 1.5 * step / 2 bounds every point between grid
    points. Outside [-20, 20] the clipped activation is linear with a slope in
    [0, 1].
    """
    lo, hi, n = -20.0, 20.0, 400_001
    z = np.linspace(lo, hi, n)
    step = (hi - lo) / (n - 1)
    return max(1.0, float(np.max(np.abs(gp(z))) + 1.5 * step / 2.0))


def cert_bound(vec0, X, R, gamma):
    """Per-input bound on ||f(w, x) - f(w0, x)||_2 over all ||w - w0|| <= R."""
    W1, b1, W2, b2, W3, b3 = split(vec0)
    _, H1, _, H2, _ = forward(vec0, X, cache=True)
    s2 = float(np.linalg.norm(W2, 2))
    s3 = float(np.linalg.norm(W3, 2))
    A0 = np.sqrt(np.sum(X ** 2, axis=1) + 1.0)
    A1 = np.sqrt(np.sum(H1 ** 2, axis=1) + 1.0)
    A2 = np.sqrt(np.sum(H2 ** 2, axis=1) + 1.0)
    c = np.sqrt((gamma ** 2 * s3 * s2 * A0) ** 2 + (gamma * s3 * A1) ** 2 + A2 ** 2)
    quad = 0.5 * (gamma ** 2 * (s2 + s3) * A0 + gamma * A1)
    cub = gamma ** 2 * A0 / (3.0 * math.sqrt(3.0))
    return R * c + R ** 2 * quad + R ** 3 * cub


def cert_rms(vec0, X, R, gamma):
    """Bound on the output RMS change over the set X for every w in the ball."""
    b = cert_bound(vec0, X, R, gamma)
    return float(np.sqrt(np.mean(b ** 2) / D_OUT))


# ---------------------------------------------------------------------------
# Adversaries
# ---------------------------------------------------------------------------

def pga(vec0, X_att, r, start, steps=80, proj=None, X_pen=None, mu=0.0):
    """Maximise the RMS change on X_att inside the ball of radius r.

    proj, if given, is an orthonormal basis Q whose span is removed from every
    step (moves stay invisible to first order on the fit probes). X_pen with
    mu adds a penalty on the change measured on the fit probes.
    """
    Y0 = forward(vec0, X_att)
    Yp0 = forward(vec0, X_pen) if X_pen is not None else None
    d = r * unit(start)
    best_d, best_v = d.copy(), -1.0
    for k in range(steps):
        w = vec0 + d
        Rm = forward(w, X_att) - Y0
        val = float(np.mean(Rm ** 2))
        grad = vjp(w, X_att, 2.0 * Rm / Rm.size)
        if X_pen is not None:
            Rp = forward(w, X_pen) - Yp0
            val -= mu * float(np.mean(Rp ** 2))
            grad -= mu * vjp(w, X_pen, 2.0 * Rp / Rp.size)
        if val > best_v:
            best_v, best_d = val, d.copy()
        if proj is not None:
            grad = grad - proj @ (proj.T @ grad)
        gn = float(np.linalg.norm(grad))
        if gn < 1e-300:
            break
        eta = 0.25 * r * (0.5 * (1.0 + math.cos(math.pi * k / steps)) + 0.05)
        d = d + eta * grad / gn
        if proj is not None:
            d = d - proj @ (proj.T @ d)
        d = r * unit(d)
    w = vec0 + d
    Rm = forward(w, X_att) - Y0
    val = float(np.mean(Rm ** 2))
    if X_pen is not None:
        val -= mu * float(np.mean((forward(w, X_pen) - Yp0) ** 2))
    if val > best_v:
        best_d = d
    return best_d


# ---------------------------------------------------------------------------
# One host
# ---------------------------------------------------------------------------

def run_host(e13, seed, gamma, quick=False):
    t0 = time.time()
    env = e13.FiveSkillEnvironment(world_seed=WORLD0 + seed)
    rng_h = np.random.default_rng(HOST0 + seed)
    host = e13.init_organism(rng_h)
    w_init = flat_org(host)
    e13.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
    w0 = flat_org(host)

    X_fit, _ = env.sample_batch(np.random.default_rng(FIT0 + seed), [0, 1], 128, shifted=False)
    rng_ho = np.random.default_rng(HELD0 + seed)
    X_ho, _ = env.sample_batch(rng_ho, [0, 1], 1024, shifted=False)
    X_sh, Y_sh = env.sample_batch(rng_ho, [0, 1], 1024, shifted=True)
    rng_at = np.random.default_rng(ATT0 + seed)
    X_att, _ = env.sample_batch(rng_at, [0, 1], 128, shifted=False)
    X_tr, Y_tr = env.sample_batch(rng_at, [0, 1], 128, shifted=False)
    X_nv, Y_nv = env.sample_batch(rng_at, [2], 256, shifted=False)

    # The forward pass written here must agree with the E13 one.
    if float(np.max(np.abs(forward(w0, X_fit) - host.predict(X_fit)))) > 1e-10:
        fail("forward pass disagrees with the E13 predict")

    Yfit0, Yho0, Ysh0 = forward(w0, X_fit), forward(w0, X_ho), forward(w0, X_sh)
    base_r2 = r2_e13(w0, X_sh, Y_sh)
    nd = X_fit.shape[0] * D_OUT

    J = jacobian(w0, X_fit)
    rng_d = np.random.default_rng(DIR0 + seed)
    # Jacobian against central differences, and against the gradient routine.
    for _ in range(4):
        u = unit(rng_d.normal(size=P))
        eps = 1e-5
        fd = (forward(w0 + eps * u, X_fit) - forward(w0 - eps * u, X_fit)).ravel() / (2 * eps)
        an = J @ u
        if float(np.max(np.abs(fd - an))) > 1e-6 * (1.0 + float(np.max(np.abs(an)))):
            fail("Jacobian disagrees with central differences")
        Rm = rng_d.normal(size=(X_fit.shape[0], D_OUT))
        if abs(float(Rm.ravel() @ an) - float(vjp(w0, X_fit, Rm) @ u)) > 1e-8 * (1.0 + abs(float(Rm.ravel() @ an))):
            fail("gradient routine disagrees with the Jacobian")

    # Spectrum of G = J'J / nd through the small matrix JJ'.
    evals, U = np.linalg.eigh(J @ J.T / nd)
    evals = np.clip(evals[::-1], 0.0, None)
    U = U[:, ::-1]
    lam_max = float(evals[0])
    trace = float(evals.sum())
    top = unit(J.T @ U[:, 0])
    Q = row_basis(J)
    rank = int(Q.shape[1])

    def fisher_q(d):
        return float(np.linalg.norm(J @ d) / math.sqrt(nd))

    rows = []

    def record(cls, d, natural=False, r_nom=None):
        w = w0 + d
        r = float(np.linalg.norm(d))
        if r_nom is not None and abs(r - r_nom) > 1e-9 * max(1.0, r_nom):
            fail(f"move of class {cls} has norm {r}, expected {r_nom}")
        row = {
            "class": cls, "natural": bool(natural), "r": r if r_nom is None else float(r_nom),
            "fisher": fisher_q(d),
            "probe": rms_change(w, w0, X_fit, Yfit0),
            "held": rms_change(w, w0, X_ho, Yho0),
            "shift": rms_change(w, w0, X_sh, Ysh0),
            "drop": base_r2 - r2_e13(w, X_sh, Y_sh),
            "cert_fit": cert_rms(w0, X_fit, r, gamma),
            "cert_held": cert_rms(w0, X_ho, r, gamma),
        }
        # Soundness of the proved bound on the inputs it was computed for.
        if row["probe"] > row["cert_fit"] * (1 + 1e-9) or row["held"] > row["cert_held"] * (1 + 1e-9):
            fail(f"proved bound violated: class {cls} r {r}")
        rows.append(row)
        return row

    # --- scalable directions -------------------------------------------------
    dirs = {}
    for k in range(5):
        dirs[f"rand{k}"] = unit(rng_d.normal(size=P))
    dirs["top"] = top
    for k in range(3):
        v = rng_d.normal(size=P)
        dirs[f"null{k}"] = unit(v - Q @ (Q.T @ v))
    res_tr = forward(w0, X_tr) - Y_tr
    g_nat = vjp(w0, X_tr, 2.0 * res_tr / res_tr.size)
    dirs["grad_native"] = unit(-g_nat)
    res_nv = forward(w0, X_nv) - Y_nv
    g_nov = vjp(w0, X_nv, 2.0 * res_nv / res_nv.size)
    dirs["grad_novel"] = unit(-g_nov)
    dirs["adam_novel"] = unit(-np.sign(g_nov))
    flip = np.zeros(P)
    flip[OFFS[4]:] = -w0[OFFS[4]:]
    dirs["flip"] = unit(flip)
    # Dormant slots: the units the E13 splice would overwrite (lowest Fisher score).
    Z1, H1, Z2, H2, _ = forward(w0, X_fit, cache=True)
    W1, b1, W2, b2, W3, b3 = split(w0)
    f1 = np.sum(W2 ** 2, axis=0) * (np.mean((H1 * gp(Z1)) ** 2, axis=0) + 1e-8)
    f2 = np.sum(W3 ** 2, axis=0) * (np.mean((H2 * gp(Z2)) ** 2, axis=0) + 1e-8)
    s1, s2 = np.argsort(f1)[:14], np.argsort(f2)[:16]
    mask = [np.zeros(s) for s in SHAPES]
    mask[0][s1, :] = 1.0
    mask[1][s1] = 1.0
    mask[2][s2, :] = 1.0
    mask[2][:, s1] = 1.0
    mask[3][s2] = 1.0
    mask[4][:, s2] = 1.0
    mvec = np.concatenate([m.ravel() for m in mask])
    dirs["dormant"] = unit(rng_d.normal(size=P) * mvec)

    radii = RADII if not quick else [0.1, 1.0, 10.0]
    for name, u in dirs.items():
        cls = name.rstrip("0123456789") if name[:4] in ("rand", "null") else name
        for r in radii:
            record(cls, r * u, r_nom=r)

    # --- natural moves ---------------------------------------------------------
    perm = e13.scramble_organism_hidden_gauge(host, np.random.default_rng(DIR0 + 7 + seed))
    record("perm", flat_org(perm) - w0, natural=True)
    record("flip", 2.0 * flip, natural=True)
    record("to_init", w_init - w0, natural=True)

    rng_dn = np.random.default_rng(DONOR0 + seed)
    donor = e13.init_organism(rng_dn)
    e13.train_organism_adam(donor, env, [0, 1, 2], rng_dn, steps=290)
    donor = e13.scramble_organism_hidden_gauge(donor, rng_dn)
    pkt = e13.extract_neural_plasmid_from_donor(donor, skill_idx=2, probe_seed=PKT0 + seed)
    rng_k = np.random.default_rng(PKT0 + 500_000 + seed)
    X_keep, _ = env.sample_batch(rng_k, [0, 1], n_per_skill=80, shifted=False)
    X_synth, _ = env.sample_batch(rng_k, [2], n_per_skill=256, shifted=False)
    X_snv, Y_snv = env.sample_batch(rng_k, [2], n_per_skill=250, shifted=True)
    graft, _ = e13.splice_gfpt_neural_plasmid(host, pkt, X_keep, X_synth,
                                              geodesic_retraction_steps=4, lateral_shunting=True)
    wg = flat_org(graft)
    grow = record("graft", wg - w0, natural=True)
    grow["novel_r2_after"] = r2_e13(wg, X_snv, Y_snv)
    grow["joint_pass"] = bool(grow["drop"] <= RETENTION_DROP_MAX and grow["novel_r2_after"] >= 0.70)

    # One optimiser step on the novel skill, as the E13 trainer would take it at
    # its first step: Adam's first update is -lr * g / (|g| + eps) with lr 0.009
    # (the trainer adds 1e-5 * W to the gradient of each weight matrix).
    g_step = g_nov.copy()
    for i in (0, 2, 4):
        g_step[OFFS[i]:OFFS[i + 1]] += 1e-5 * w0[OFFS[i]:OFFS[i + 1]]
    record("one_step", -0.009 * g_step / (np.abs(g_step) + 1e-8), natural=True)
    # Learning the novel skill by ordinary training, with the native data at hand:
    # 120 more steps on all three skills. What that costs in distance.
    ft_org = to_org(e13, w0)
    e13.train_organism_adam(ft_org, env, [0, 1, 2], np.random.default_rng(DIR0 + 11 + seed), steps=120)
    ft_row = record("finetune_joint", flat_org(ft_org) - w0, natural=True)
    ft_row["novel_r2_after"] = r2_e13(flat_org(ft_org), X_snv, Y_snv)
    ft_row["joint_pass"] = bool(ft_row["drop"] <= RETENTION_DROP_MAX and ft_row["novel_r2_after"] >= 0.70)

    # --- adversaries inside the ball -------------------------------------------
    J_att = jacobian(w0, X_att)
    ev_a, U_a = np.linalg.eigh(J_att @ J_att.T / (X_att.shape[0] * D_OUT))
    top_att = unit(J_att.T @ U_a[:, -1])
    null_start = unit(top_att - Q @ (Q.T @ top_att))
    adv_radii = radii
    for r in adv_radii:
        d = pga(w0, X_att, r, top_att, steps=30 if quick else 80)
        record("adv", d, r_nom=r)
        d = pga(w0, X_att, r, null_start, steps=30 if quick else 80, proj=Q, X_pen=X_fit, mu=100.0)
        record("adv_blind", d, r_nom=r)

    # --- radii --------------------------------------------------------------------
    def r_break(cls):
        """Smallest tested radius at which the class breaks the retention bar."""
        hit = [x["r"] for x in rows if x["class"] == cls and not x["natural"] and x["drop"] > RETENTION_DROP_MAX]
        return min(hit) if hit else None

    def cert_radius(tau):
        lo, hi = 0.0, 1.0
        while cert_rms(w0, X_ho, hi, gamma) < tau:
            hi *= 2.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if cert_rms(w0, X_ho, mid, gamma) <= tau:
                lo = mid
            else:
                hi = mid
        return lo

    y_scale = float(np.sqrt(np.mean(Ysh0 ** 2)))
    summary = {
        "seed": seed,
        "drop_metric": "shifted native R2 (E13 definition), bar 0.025",
        "n_weights": P,
        "weight_norm": float(np.linalg.norm(w0)),
        "base_shift_r2": base_r2,
        "output_rms_shift": y_scale,
        "lam_max": lam_max,
        "sqrt_lam_max": math.sqrt(lam_max),
        "sqrt_mean_lam": math.sqrt(trace / P),
        "anisotropy": math.sqrt(lam_max * P / trace),
        "rank_fit": rank,
        "effective_rank": float(trace / lam_max),
        "r_break": {c: r_break(c) for c in ["adv", "top", "grad_native", "grad_novel", "adam_novel", "rand", "flip", "null", "dormant", "adv_blind"]},
        "cert_radius_tau_0p05": cert_radius(0.05),
        "cert_radius_tau_0p5": cert_radius(0.5),
        "first_order_radius_tau_0p05": 0.05 / math.sqrt(lam_max),
        "seconds": time.time() - t0,
    }
    return {"summary": summary, "rows": rows}


# ---------------------------------------------------------------------------
# Analysis, shared by pilot and confirmatory runs
# ---------------------------------------------------------------------------

FLOOR = 1e-9
# Moves made without sight of the fit probes, and moves built from them.
LOCAL = ("rand", "adv", "grad_native", "grad_novel", "adam_novel", "flip", "dormant")
PROBE_AWARE = ("adv_blind", "null", "top")


def ratio(target, pred):
    if target < FLOOR and pred < FLOOR:
        return None                      # both zero: the predictor is right
    if pred < FLOOR:
        return math.inf
    return target / pred


def near(a, b):
    return abs(a - b) <= 1e-9 * max(1.0, abs(b))


def analyse(hosts, r_loc=0.1, r_blind=1.0, shipped_radius=10.0):
    """Per-host numbers and the count of hosts on which each prediction holds.

    r_loc is the radius up to which a move counts as local, r_blind the radius
    at which the probe-aware adversary is scored, shipped_radius the smaller
    shipped gate radius (None when the model has no shipped gate). A prediction
    that needs a class the run does not have is reported as None.
    """
    out = {"n_hosts": len(hosts), "per_host": [], "tests": {}}
    for h in hosts:
        rows, s = h["rows"], h["summary"]
        classes = {x["class"] for x in rows}

        def pick(cls, r=None, natural=False):
            return [x for x in rows if x["class"] == cls and x["natural"] == natural
                    and (r is None or near(x["r"], r))]

        ph = {"seed": s["seed"], "anisotropy": s["anisotropy"]}
        rand01 = float(np.median([x["held"] for x in pick("rand", r_loc)]))
        ph["H1_top_over_rand"] = pick("top", r_loc)[0]["held"] / rand01
        perm = pick("perm", natural=True)[0]
        ph["H1_perm_r"], ph["H1_perm_held"], ph["H1_perm_fisher"] = perm["r"], perm["held"], perm["fisher"]
        loc = [x for x in rows if not x["natural"] and x["r"] <= r_loc * (1 + 1e-9) and x["class"] in LOCAL]
        r_in = [x["probe"] / x["fisher"] for x in loc]
        r_out = [x["held"] / x["fisher"] for x in loc]
        ph["H2_probe_over_fisher_min"], ph["H2_probe_over_fisher_max"] = min(r_in), max(r_in)
        ph["H2_held_over_fisher_min"], ph["H2_held_over_fisher_max"] = min(r_out), max(r_out)
        tp = pick("top", r_loc)[0]
        ph["top_held_over_probe"] = tp["held"] / tp["probe"]
        nul = pick("null", r_loc)
        ph["H3_null_fisher_max"] = max(x["fisher"] for x in nul)
        ph["H3_null_held_min"] = min(x["held"] for x in nul)
        nat = [x for x in rows if x["natural"] and x["class"] in ("perm", "graft", "finetune_joint", "to_init")]
        rn = [ratio(x["held"], x["fisher"]) for x in nat]
        rn = [v for v in rn if v is not None]
        ph["H3_natural_held_over_fisher_min"], ph["H3_natural_held_over_fisher_max"] = min(rn), max(rn)
        gen = [x for x in rows if x["class"] not in PROBE_AWARE and x["held"] >= 1e-6]
        rg = [ratio(x["held"], x["probe"]) for x in gen]
        ph["H4_held_over_probe_min"], ph["H4_held_over_probe_max"] = min(rg), max(rg)
        ph["H4_perm_probe"] = perm["probe"]
        ab = pick("adv_blind", r_blind)[0]
        ph["H5_blind_held"], ph["H5_blind_probe"] = ab["held"], ab["probe"]
        ph["H5_blind_ratio"] = ratio(ab["held"], ab["probe"])
        ph["H6_r_break_adv"] = s["r_break"]["adv"]
        ph["H6_r_break_rand"] = s["r_break"]["rand"]
        ph["H6_one_step_r"] = pick("one_step", natural=True)[0]["r"]
        ft = pick("finetune_joint", natural=True)[0]
        ph["H6_finetune_r"], ph["H6_finetune_joint_pass"] = ft["r"], ft.get("joint_pass")
        if "graft" in classes:
            gr = pick("graft", natural=True)[0]
            ph["H6_graft_r"], ph["H6_graft_joint_pass"] = gr["r"], gr["joint_pass"]
            ph["H6_graft_probe"] = gr["probe"]
            # Largest radius at which the probe-aware adversary still shows less
            # change on the fit probes than the benign graft does, and what it
            # does to the model there.
            under = [x for x in rows if x["class"] == "adv_blind" and x["probe"] <= gr["probe"]]
            worst = max(under, key=lambda x: x["drop"]) if under else None
            ph["H5_blind_under_graft_drop"] = worst["drop"] if worst else None
            ph["H5_blind_under_graft_r"] = worst["r"] if worst else None
        if "cert_radius_tau_0p05" in s:
            ph["H7_cert_radius_0p05"] = s["cert_radius_tau_0p05"]
            adv_hit = [x["r"] for x in rows if x["class"] == "adv" and x["held"] >= 0.05]
            ph["H7_attack_radius_0p05"] = min(adv_hit) if adv_hit else None
        out["per_host"].append(ph)

    ph = out["per_host"]

    def count(pred, need=None):
        if need is not None and not all(need in x for x in ph):
            return None
        return int(sum(1 for x in ph if pred(x)))

    t = out["tests"]
    t["n_hosts"] = len(ph)
    t["r_loc"], t["r_blind"] = r_loc, r_blind
    t["H1a_top_over_rand_ge_10"] = count(lambda x: x["H1_top_over_rand"] >= 10.0)
    t["H1b_perm_far_and_silent"] = count(lambda x: x["H6_r_break_adv"] is not None and x["H1_perm_r"] >= 30.0 * x["H6_r_break_adv"] and x["H1_perm_held"] <= 1e-9)
    t["H2a_fisher_within_1p1_on_fit_probes"] = count(lambda x: 1 / 1.1 <= x["H2_probe_over_fisher_min"] and x["H2_probe_over_fisher_max"] <= 1.1)
    t["H2b_fisher_within_1p25_on_held"] = count(lambda x: 0.8 <= x["H2_held_over_fisher_min"] and x["H2_held_over_fisher_max"] <= 1.25)
    t["H3a_fisher_blind_to_null_moves"] = count(lambda x: x["H3_null_fisher_max"] <= 1e-9 and x["H3_null_held_min"] >= 1e-6)
    t["H3b_fisher_off_by_3_on_a_natural_move"] = count(lambda x: x["H3_natural_held_over_fisher_min"] < 1 / 3 or x["H3_natural_held_over_fisher_max"] > 3.0)
    t["H4_probe_within_1p25_on_held"] = count(lambda x: 0.8 <= x["H4_held_over_probe_min"] and x["H4_held_over_probe_max"] <= 1.25 and x["H4_perm_probe"] <= 1e-9)
    t["H5a_blind_adversary_ratio_ge_10"] = count(lambda x: x["H5_blind_ratio"] is not None and x["H5_blind_ratio"] >= 10.0)
    t["H5b_blind_adversary_breaks_bar_under_graft_level"] = count(lambda x: x["H5_blind_under_graft_drop"] is not None and x["H5_blind_under_graft_drop"] > RETENTION_DROP_MAX, need="H5_blind_under_graft_drop")
    t["H6a_adv_breaks_10x_before_rand"] = count(lambda x: x["H6_r_break_adv"] is not None and (x["H6_r_break_rand"] is None or 10.0 * x["H6_r_break_adv"] <= x["H6_r_break_rand"] * (1 + 1e-9)))
    t["H6b_one_step_ge_r_break_adv"] = count(lambda x: x["H6_r_break_adv"] is not None and x["H6_one_step_r"] >= x["H6_r_break_adv"])
    t["H6c_graft_passes_at_r_ge_20"] = count(lambda x: x["H6_graft_r"] >= 20.0 and x["H6_graft_joint_pass"], need="H6_graft_r")
    t["H6d_rand_breaks_inside_shipped_radius"] = None if shipped_radius is None else count(
        lambda x: x["H6_r_break_rand"] is not None and x["H6_r_break_rand"] <= shipped_radius * (1 + 1e-9))
    t["H7_cert_le_attack"] = count(lambda x: x["H7_attack_radius_0p05"] is not None and x["H7_cert_radius_0p05"] <= x["H7_attack_radius_0p05"], need="H7_cert_radius_0p05")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    e13 = load_e13()
    gamma = gelu_slope_bound()
    if not (1.09 < gamma < 1.11):
        fail(f"unexpected slope bound {gamma}")
    hosts = []
    for s in a.seeds:
        h = run_host(e13, s, gamma, quick=a.quick)
        hosts.append(h)
        sm = h["summary"]
        print(f"seed {s}: |w|={sm['weight_norm']:.3f} R2={sm['base_shift_r2']:.4f} "
              f"sqrt(lam_max)={sm['sqrt_lam_max']:.3f} anisotropy={sm['anisotropy']:.1f} "
              f"r_break(adv)={sm['r_break']['adv']} cert_radius(0.05)={sm['cert_radius_tau_0p05']:.3e} "
              f"[{sm['seconds']:.0f}s]", flush=True)
    res = {
        "program_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "e13_sha256": hashlib.sha256(E13_PATH.read_bytes()).hexdigest(),
        "numpy": np.__version__,
        "python": sys.version.split()[0],
        "gelu_slope_bound": gamma,
        "seeds": a.seeds,
        "quick": bool(a.quick),
        "hosts": hosts,
    }
    if not a.quick:
        res["analysis"] = analyse(hosts)
        print(json.dumps(res["analysis"]["tests"], indent=1))
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
