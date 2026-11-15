#!/usr/bin/env python3
"""Causal capacity: how many independent directions a network can carry (facts 10 to 12 of the note).

A unit computes a function of the units that feed it through open weights.
The capacity of a network is the largest number of paths from inputs to
outputs, along open weights, that share no unit. By Menger's theorem it is
also the size of the smallest set of units that every such path meets.

Stage A checks the statements on random sparse networks:
  - capacity is certified both ways: a family of disjoint paths and a cut of the same size;
  - the outputs depend on the inputs only through the units of the cut
    (clamp the cut, change the inputs, and no output moves);
  - the rank of the input-to-output map is at most the capacity for any
    weights, and equal to it for random weights.
Stage B measures the demand of a skill by intervention on the data generator
itself: each input is moved in turn and the generator is run again.
Stage C trains networks with a narrow layer of width c and compares the
knee of their score with that demand.
Stage D takes the 12 MLP hosts of the calibration record: their capacity
as weights are pruned, and what closing the weights out of the inputs that
the data's formula never uses does to the native score.

PREDICTIONS, written and committed before stages C and D were run.
  C1. One skill: at width 3 and below, the score is more than 0.025 under the dense network's on every seed.
  C2. One skill: at width 8 and above, the score is within 0.025 of the dense network's on every seed.
  C3. One skill: the knee, the smallest width within 0.025 of dense, is 4, 5 or 6 on every seed.
  C4. Two skills: at width 4 and below the score is more than 0.025 under dense on every seed, and the knee is larger than for one skill.
  D1. Pruning by magnitude breaks the retention bar while the capacity is still 8 on every host. The cut does not see that failure.
  D2. Closing the 288 weights out of the three nuisance inputs lowers the native score under shift on no more than 2 of 12 hosts,
      and changes the score without shift by less than 0.01 on all 12.
C1 to C4 are judged on the longer training (1,120 steps).

Needs NumPy. Usage, from the root of a checkout:
  python3 notes/prototypes/closure-register/causal_capacity.py > notes/prototypes/closure-register/causal_capacity.out
  python3 notes/prototypes/closure-register/causal_capacity.py --stages AB     # the checks only
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from closure_balls import load_calib  # noqa: E402

BAR = 0.025
BIG = 10 ** 6


# ---------------------------------------------------------------------------
# Capacity, with both certificates
# ---------------------------------------------------------------------------

def capacity(masks):
    """masks[l][j, i] is true if unit i of layer l feeds unit j of layer l+1 through an open weight.

    Returns (c, paths, cut): c vertex-disjoint paths from layer 0 to the last
    layer, each a list of (layer, unit), and a set of c units that every such
    path meets. Unit-capacity flow with each unit split in two.
    """
    sizes = [masks[0].shape[1]] + [m.shape[0] for m in masks]
    node = {}
    for l, s in enumerate(sizes):
        for u in range(s):
            node[(l, u, 0)] = len(node)
            node[(l, u, 1)] = len(node)
    S, T = len(node), len(node) + 1
    cap, adj = {}, {}

    def add(a, b, c):
        cap[(a, b)] = c
        cap[(b, a)] = 0
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    for l, s in enumerate(sizes):
        for u in range(s):
            add(node[(l, u, 0)], node[(l, u, 1)], 1)
    for u in range(sizes[0]):
        add(S, node[(0, u, 0)], BIG)
    for u in range(sizes[-1]):
        add(node[(len(sizes) - 1, u, 1)], T, BIG)
    for l, m in enumerate(masks):
        for j, i in zip(*np.nonzero(m)):
            add(node[(l, int(i), 1)], node[(l + 1, int(j), 0)], BIG)
    full = dict(cap)

    def reach():
        prev, todo = {S: None}, [S]
        while todo:
            a = todo.pop()
            for b in adj.get(a, []):
                if b not in prev and cap[(a, b)] > 0:
                    prev[b] = a
                    todo.append(b)
        return prev

    flow = 0
    while True:
        prev = reach()
        if T not in prev:
            break
        b = T
        while prev[b] is not None:
            a = prev[b]
            cap[(a, b)] -= 1
            cap[(b, a)] += 1
            b = a
        flow += 1
    cut = {(l, u) for (l, u, half) in node if half == 0 and node[(l, u, 0)] in prev and node[(l, u, 1)] not in prev}
    back = {v: k for k, v in node.items()}
    used = {(a, b): full[(a, b)] - cap[(a, b)] for (a, b) in full if full[(a, b)] > cap[(a, b)]}
    paths = []
    for u in range(sizes[0]):
        if used.get((S, node[(0, u, 0)]), 0) > 0:
            a, path = node[(0, u, 0)], []
            while a != T:
                l, v, half = back[a]
                if half == 0:
                    path.append((l, v))
                a = next(b for b in adj[a] if used.get((a, b), 0) > 0)
            paths.append(path)
    return flow, paths, cut


def certificates_hold(masks, c, paths, cut):
    """Independent check: the paths are disjoint and open, and no path survives the removal of the cut."""
    sizes = [masks[0].shape[1]] + [m.shape[0] for m in masks]
    last = len(sizes) - 1
    seen = set()
    for p in paths:
        if p[0][0] != 0 or p[-1][0] != last or any(v in seen for v in p):
            return False
        seen |= set(p)
        for (l, i), (l2, j) in zip(p, p[1:]):
            if l2 != l + 1 or not masks[l][j, i]:
                return False
    alive = {(0, u) for u in range(sizes[0])} - cut
    for l, m in enumerate(masks):
        nxt = set()
        for (ll, i) in alive:
            if ll == l:
                nxt |= {(l + 1, int(j)) for j in np.nonzero(m[:, i])[0]}
        alive |= nxt - cut
    blocked = not any((last, u) in alive for u in range(sizes[-1]))
    return len(paths) == c and len(cut) == c and blocked


def gelu(z):
    return z / (1.0 + np.exp(-1.702 * z))


def gelu_slope(z):
    g = 1.0 / (1.0 + np.exp(-1.702 * z))
    return g + 1.702 * z * g * (1.0 - g)


def run_net(Ws, bs, x, act, clamp=None):
    """Forward pass of one input. clamp maps (layer, unit) to a value that overrides the unit."""
    clamp = clamp or {}
    h = x.copy()
    values = {}
    for u in range(len(h)):
        if (0, u) in clamp:
            h[u] = clamp[(0, u)]
        values[(0, u)] = h[u]
    for l, (W, b) in enumerate(zip(Ws, bs)):
        z = W @ h + b
        h = z if l == len(Ws) - 1 else act(z)
        for u in range(len(h)):
            if (l + 1, u) in clamp:
                h[u] = clamp[(l + 1, u)]
            values[(l + 1, u)] = h[u]
    return h, values


def jacobian_fd(f, x, eps=1e-6):
    cols = []
    for k in range(len(x)):
        d = np.zeros(len(x))
        d[k] = eps
        cols.append((f(x + d) - f(x - d)) / (2 * eps))
    return np.array(cols).T


def stage_a(n_nets=300):
    rng = np.random.default_rng(20261115)
    ok_cert = le_lin = eq_lin = eq_tanh = eq_gelu = clamp_ok = 0
    worst = 0.0
    for _ in range(n_nets):
        sizes = [int(rng.integers(3, 9)) for _ in range(int(rng.integers(3, 6)))]
        p = rng.choice([0.25, 0.4, 0.6])
        masks = [rng.random((sizes[l + 1], sizes[l])) < p for l in range(len(sizes) - 1)]
        c, paths, cut = capacity(masks)
        ok_cert += certificates_hold(masks, c, paths, cut)
        Ws = [m * rng.normal(size=m.shape) for m in masks]
        bs = [0.3 * rng.normal(size=m.shape[0]) for m in masks]
        M = np.eye(sizes[0])
        for W in Ws:
            M = W @ M
        r = int(np.linalg.matrix_rank(M, tol=1e-9))
        le_lin += r <= c
        eq_lin += r == c
        x, x2 = rng.normal(size=sizes[0]), rng.normal(size=sizes[0])
        for name, act, slope in (("tanh", np.tanh, lambda z: 1.0 - np.tanh(z) ** 2), ("gelu", gelu, gelu_slope)):
            # The Jacobian in closed form: each layer's weights times the slopes of its units.
            J, h = np.eye(sizes[0]), x
            for l, (W, b) in enumerate(zip(Ws, bs)):
                z = W @ h + b
                last = l == len(Ws) - 1
                J = (W if last else slope(z)[:, None] * W) @ J
                h = z if last else act(z)
            sv = np.linalg.svd(J, compute_uv=False)
            rj = int(np.sum(sv > 1e-10 * sv[0])) if sv[0] > 0 else 0
            if rj > c:
                raise SystemExit("FAIL: a Jacobian has rank above the capacity")
            if name == "tanh":
                eq_tanh += rj == c
            else:
                eq_gelu += rj == c
        y, values = run_net(Ws, bs, x, gelu)
        y2, _ = run_net(Ws, bs, x2, gelu, clamp={v: values[v] for v in cut})
        diff = float(np.max(np.abs(y - y2))) if len(y) else 0.0
        worst = max(worst, diff)
        clamp_ok += diff <= 1e-12
    print("Stage A. Random sparse networks")
    print(f"   networks: {n_nets}")
    print(f"   capacity certified both ways (disjoint paths and a cut of the same size): {ok_cert}")
    print(f"   cut clamped, inputs changed, no output moved: {clamp_ok} (largest change {worst:.1e})")
    print(f"   linear network, random weights: rank at most the capacity on {le_lin}, equal on {eq_lin}")
    print(f"   Jacobian rank equal to the capacity at a random input: tanh {eq_tanh}, GELU {eq_gelu}")
    if not (ok_cert == clamp_ok == le_lin == n_nets):
        raise SystemExit("FAIL: a statement that holds for all weights failed")
    return eq_lin, eq_tanh, eq_gelu


# ---------------------------------------------------------------------------
# The demand of a skill, from the generator's formula
# ---------------------------------------------------------------------------

class Fixed:
    """Stands in for the random generator, so that the data generator runs on inputs we choose."""

    def __init__(self, arrays):
        self.arrays = list(arrays)

    def normal(self, loc, scale, size):
        return self.arrays.pop(0)

    def uniform(self, low, high, size):
        return self.arrays.pop(0)


def generator_at(env, m, X):
    """Outputs of the data generator itself for skill m at chosen inputs X of shape (n, 24).

    sample_batch draws the state, the nuisance inputs, a gate amplitude and gate
    noise, in that order. Feeding it those four arrays makes it evaluate at X.
    """
    z, gates, nuis = X[:, :16].copy(), X[:, 16:21].copy(), X[:, 21:24].copy()
    gates[:, m] -= 2.4
    Xg, Y = env.sample_batch(Fixed([z, nuis, np.ones((len(X), 1)), gates]), [m], len(X), shifted=False)
    if float(np.max(np.abs(Xg - X))) > 1e-12:
        raise SystemExit("FAIL: the data generator was not evaluated at the chosen inputs")
    return Y


def stage_b(e13):
    print("\nStage B. The demand of a skill, by intervention on the data generator")
    print("   By its formula an output of skill m depends on the input only through 4 numbers, the projections of z on U_sub[m],")
    print("   and the skill's own gate. That is 5 directions. The other 4 gates and the 3 nuisance inputs have no effect.")
    print("   Here each of the 24 inputs is moved in turn, up and down by 1e-6, and the generator is run again.")
    env = e13.FiveSkillEnvironment(world_seed=61_000_000)
    rng = np.random.default_rng(64_000_000)
    eps = 1e-6
    for m in (0, 1):
        X, Y = env.sample_batch(rng, [m], 200, shifted=False)
        if float(np.max(np.abs(generator_at(env, m, X) - Y))) > 1e-12:
            raise SystemExit("FAIL: the generator run on chosen inputs disagrees with its own samples")
        ranks, profile, inert = [], [], 0.0
        for x in X:
            up = generator_at(env, m, x[None, :] + eps * np.eye(24))
            down = generator_at(env, m, x[None, :] - eps * np.eye(24))
            J = ((up - down) / (2 * eps)).T
            s = np.linalg.svd(J, compute_uv=False)
            ranks.append(int(np.sum(s > 1e-6 * s[0])))
            profile.append(s / s[0])
            dead = [16 + k for k in range(5) if k != m] + [21, 22, 23]
            inert = max(inert, float(np.max(np.abs(J[:, dead]))))
        prof = np.median(np.array(profile), axis=0)
        print(f"   skill {m}: Jacobian rank at 200 inputs: least {min(ranks)}, most {max(ranks)}; "
              f"median singular values over the largest: {', '.join(f'{v:.3f}' for v in prof)}")
        print(f"            largest effect of the 7 unused inputs: {inert:.1e}")


# ---------------------------------------------------------------------------
# Networks with a narrow layer
# ---------------------------------------------------------------------------

WIDTHS = (1, 2, 3, 4, 5, 6, 8, 12, 16, 96)


def stage_c(e13):
    print("\nStage C. Networks 24 -> 96 -> c -> 8 trained on the generator, score R2 on 1,024 fresh inputs per skill")
    for skills, label in (([0], "one skill"), ([0, 1], "two skills")):
        for steps in (280, 1120):
            print(f"   {label}, {steps} training steps")
            print("   seed | " + " | ".join(f"c={c:<3}" for c in WIDTHS) + " | knee")
            knees = []
            table = []
            for seed in range(3):
                env = e13.FiveSkillEnvironment(world_seed=61_000_000 + seed)
                Xe, Ye = env.sample_batch(np.random.default_rng(63_000_000 + seed), skills, 1024, shifted=False)
                row = []
                for c in WIDTHS:
                    rng = np.random.default_rng(62_000_000 + 1000 * c + 10 * len(skills) + seed)
                    org = e13.MultiLayerOrganism(
                        W1=rng.normal(0.0, math.sqrt(2.0 / 24), size=(96, 24)), b1=np.zeros(96),
                        W2=rng.normal(0.0, math.sqrt(2.0 / 96), size=(c, 96)), b2=np.zeros(c),
                        W3=rng.normal(0.0, math.sqrt(1.0 / c), size=(8, c)), b3=np.zeros(8))
                    e13.train_organism_adam(org, env, skills, rng, steps=steps)
                    row.append(e13.eval_skill_r2(org, Xe, Ye))
                knee = next(c for c, v in zip(WIDTHS, row) if v >= row[-1] - BAR)
                knees.append(knee)
                table.append(row)
                print(f"   {seed:>4} | " + " | ".join(f"{v:5.3f}" for v in row) + f" | {knee}")
            yield label, steps, table, knees


def judge_c(results):
    r = {(label, steps): (table, knees) for label, steps, table, knees in results}
    one, k1 = r[("one skill", 1120)]
    two, k2 = r[("two skills", 1120)]
    idx = {c: i for i, c in enumerate(WIDTHS)}
    c1 = all(row[idx[c]] < row[-1] - BAR for row in one for c in (1, 2, 3))
    c2 = all(row[idx[c]] >= row[-1] - BAR for row in one for c in (8, 12, 16))
    c3 = all(k in (4, 5, 6) for k in k1)
    c4 = all(row[idx[c]] < row[-1] - BAR for row in two for c in (1, 2, 3, 4)) and all(b > a for a, b in zip(k1, k2))
    print("   judged on 1,120 steps:")
    print(f"   C1 one skill, width 3 and below more than {BAR} under dense on every seed: {'holds' if c1 else 'FAILS'}")
    print(f"   C2 one skill, width 8 and above within {BAR} of dense on every seed: {'holds' if c2 else 'FAILS'}")
    print(f"   C3 one skill, knee at 4, 5 or 6 on every seed: {'holds' if c3 else 'FAILS'} (knees {k1})")
    print(f"   C4 two skills, width 4 and below under dense, and a larger knee than one skill: {'holds' if c4 else 'FAILS'} (knees {k2})")


# ---------------------------------------------------------------------------
# The calibration hosts
# ---------------------------------------------------------------------------

KEEP = (1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.002)


def prune(c, vec, keep):
    out = []
    for a in c.split(vec):
        if a.ndim == 2 and keep < 1.0:
            k = max(1, int(round(keep * a.size)))
            thr = np.sort(np.abs(a).ravel())[-k]
            out.append(np.where(np.abs(a) >= thr, a, 0.0))
        else:
            out.append(a.copy())
    return np.concatenate([a.ravel() for a in out])


def stage_d(e13):
    c = load_calib()
    print("\nStage D. The 12 MLP hosts of the calibration record")
    rows = {k: [] for k in KEEP}
    close = []
    for seed in range(12):
        env = e13.FiveSkillEnvironment(world_seed=c.WORLD0 + seed)
        rng_h = np.random.default_rng(c.HOST0 + seed)
        host = e13.init_organism(rng_h)
        e13.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
        w0 = c.flat_org(host)
        rng_ho = np.random.default_rng(c.HELD0 + seed)
        X_ho, Y_ho = env.sample_batch(rng_ho, [0, 1], 1024, shifted=False)
        X_sh, Y_sh = env.sample_batch(rng_ho, [0, 1], 1024, shifted=True)
        base_sh, base_in = c.r2_e13(w0, X_sh, Y_sh), c.r2_e13(w0, X_ho, Y_ho)
        for keep in KEEP:
            w = prune(c, w0, keep)
            W1, _, W2, _, W3, _ = c.split(w)
            cap, paths, cut = capacity([W1 != 0, W2 != 0, W3 != 0])
            if not certificates_hold([W1 != 0, W2 != 0, W3 != 0], cap, paths, cut):
                raise SystemExit("FAIL: capacity certificates do not hold on a pruned host")
            rows[keep].append((cap, base_sh - c.r2_e13(w, X_sh, Y_sh)))
        parts = [a.copy() for a in c.split(w0)]
        parts[0][:, 21:24] = 0.0
        wc = np.concatenate([a.ravel() for a in parts])
        close.append((base_sh, c.r2_e13(wc, X_sh, Y_sh), base_in, c.r2_e13(wc, X_ho, Y_ho),
                      float(np.linalg.norm(wc - w0)), c.rms_change(wc, w0, X_ho)))
    print("   Pruning each weight matrix by magnitude")
    print("   share of weights kept | capacity, least to most over hosts | drop in native score, least to most | hosts keeping the bar")
    first_fail = None
    for keep in KEEP:
        caps = [a for a, _ in rows[keep]]
        drops = [b for _, b in rows[keep]]
        kept = sum(d <= BAR for d in drops)
        if first_fail is None and kept < 12:
            first_fail = (keep, min(caps))
        print(f"   {keep:>21g} | {min(caps)} to {max(caps)} | {min(drops):.4f} to {max(drops):.4f} | {kept}")
    d1 = first_fail is not None and first_fail[1] == 8
    print(f"   D1 the bar first breaks at a kept share of {first_fail[0] if first_fail else 'none'}, where the least capacity is "
          f"{first_fail[1] if first_fail else '-'}: {'holds' if d1 else 'FAILS'}")
    print("   Closing the 288 weights out of the three nuisance inputs, which the generator's formula never uses")
    print("   host | native score under shift, before and after | without shift, before and after | length of the change | RMS change of outputs on held-out inputs")
    for seed, (a, b, a2, b2, r, ch) in enumerate(close):
        print(f"   {seed:>4} | {a:.4f} -> {b:.4f} ({b - a:+.4f}) | {a2:.4f} -> {b2:.4f} ({b2 - a2:+.4f}) | {r:.3f} | {ch:.4f}")
    worse = sum(b < a for a, b, *_ in close)
    small = all(abs(b2 - a2) < 0.01 for _, _, a2, b2, *_ in close)
    gain = [b - a for a, b, *_ in close]
    print(f"   under shift the score rose on {sum(g > 0 for g in gain)} of 12 hosts, by {min(gain):+.4f} to {max(gain):+.4f}; "
          f"it fell on {worse}")
    print(f"   D2 falls on no more than 2 hosts under shift, and moves by less than 0.01 without shift on all 12: "
          f"{'holds' if worse <= 2 and small else 'FAILS'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="ABCD")
    a = ap.parse_args()
    c = load_calib()
    e13 = c.load_e13()
    if "A" in a.stages:
        stage_a()
    if "B" in a.stages:
        stage_b(e13)
    if "C" in a.stages:
        judge_c(list(stage_c(e13)))
    if "D" in a.stages:
        stage_d(e13)


if __name__ == "__main__":
    main()
