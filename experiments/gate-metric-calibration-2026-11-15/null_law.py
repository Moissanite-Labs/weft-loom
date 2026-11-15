#!/usr/bin/env python3
"""How safe is an edit inside the null space of a keep set, as the keep set grows?

Exploratory, not part of the preregistration. THEORY.md section 6 says a move
in the null space of the keep inputs changes those inputs only at second
order, and leaks at first order onto inputs outside the keep set. This program
measures both on E13 hosts for keep sets of growing size n:

  nullity   P - rank(J_keep): how many silent directions are left to edit in
  leak      held-out RMS change per unit of distance, for random null moves
  c2        change on the keep inputs divided by r squared, at r = 1
  rand      the same per-unit change for a random move, for comparison

Usage: python3 null_law.py --seeds 900 901 --out null_law.json
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np

import calib as C


def run(e13, seed, sizes):
    env = e13.FiveSkillEnvironment(world_seed=C.WORLD0 + seed)
    rng_h = np.random.default_rng(C.HOST0 + seed)
    host = e13.init_organism(rng_h)
    e13.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
    w0 = C.flat_org(host)
    pool, _ = env.sample_batch(np.random.default_rng(C.FIT0 + 7_000 + seed), [0, 1], max(sizes) // 2, shifted=False)
    half = pool.shape[0] // 2
    order = np.ravel(np.column_stack([np.arange(half), half + np.arange(half)]))   # alternate the two skills
    pool = pool[order]
    X_ho, _ = env.sample_batch(np.random.default_rng(C.HELD0 + 7_000 + seed), [0, 1], 1024, shifted=False)
    Yho0 = C.forward(w0, X_ho)
    rng_d = np.random.default_rng(C.DIR0 + 7_000 + seed)
    rand = statistics.mean(
        C.rms_change(w0 + 0.1 * C.unit(rng_d.normal(size=C.P)), w0, X_ho, Yho0) / 0.1 for _ in range(5))
    rows = []
    for n in sizes:
        Xk = pool[:n]
        J = C.jacobian(w0, Xk)
        Q = C.row_basis(J)
        Yk0 = C.forward(w0, Xk)
        leak, c2, fo = [], [], []
        for _ in range(3):
            v = rng_d.normal(size=C.P)
            u = C.unit(v - Q @ (Q.T @ v))
            fo.append(float(np.linalg.norm(J @ u)))
            leak.append(C.rms_change(w0 + 0.1 * u, w0, X_ho, Yho0) / 0.1)
            c2.append(C.rms_change(w0 + 1.0 * u, w0, Xk, Yk0))
        if max(fo) > 1e-8:
            C.fail(f"null move is visible to first order on the keep set: {max(fo)}")
        rows.append({"n_keep": n, "rows": n * C.D_OUT, "nullity": C.P - int(Q.shape[1]),
                     "leak": statistics.mean(leak), "leak_over_rand": statistics.mean(leak) / rand,
                     "c2": statistics.mean(c2)})
    return {"seed": seed, "rand_per_unit": rand, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sizes = [16, 32, 64, 128, 256, 512]
    e13 = C.load_e13()
    hosts = [run(e13, s, sizes) for s in a.seeds]
    table = []
    for i, n in enumerate(sizes):
        rs = [h["rows"][i] for h in hosts]
        table.append({"n_keep": n, "rows": rs[0]["rows"],
                      "nullity_median": statistics.median(r["nullity"] for r in rs),
                      "leak_over_rand_median": float(f"{statistics.median(r['leak_over_rand'] for r in rs):.3g}"),
                      "c2_median": float(f"{statistics.median(r['c2'] for r in rs):.3g}")})
    Path(a.out).write_text(json.dumps({"seeds": a.seeds, "n_weights": C.P, "hosts": hosts, "table": table},
                                      indent=1, sort_keys=True) + "\n")
    print("| Keep inputs | Rows of J | Silent directions left | Leak onto held-out inputs, share of a random move | Second-order change on the keep set at r = 1 |")
    print("|---|---|---|---|---|")
    for t in table:
        print(f"| {t['n_keep']} | {t['rows']} | {t['nullity_median']:g} | {t['leak_over_rand_median']:g} | {t['c2_median']:g} |")


if __name__ == "__main__":
    main()
