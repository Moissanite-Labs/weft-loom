#!/usr/bin/env python3
"""Two gates the Frobenius ball could be traded for, put to the closure rule.

Part 1, the permutation-quotient ball. Relabelling the hidden units of a layer
changes the weights and no output, so a gate could measure distance after the
best relabelling: d_perm(w, w0) = min over relabellings of ||relabelled w - w0||.
For every relabelling, each layer's block [W | b] keeps its singular values, and
Mirsky's theorem bounds the Frobenius distance between two matrices from below
by the distance between their sorted singular values. So

    d_perm(w, w0)^2 >= sum over layers of ||sv([W | b]) - sv([W0 | b0])||^2.

The program rebuilds the passing fine-tune of each MLP host of the calibration
record, checks it against the recorded row, and computes that lower bound. The
breaking move of the record has a quotient distance of at most its own length.

Part 2, a rounded copy of the cell. Each weight matrix is rounded to 2^b evenly
spaced levels (mid-rise, step 2 max|W| / 2^b, biases kept). The program measures
the length of the rounding error, the change it makes on the held-out inputs,
and the drop in the native score. It then compares the smallest step the grid
allows with the radius Theorem 1 proves within tolerance around the rounded
cell.

Needs NumPy. Usage, from the root of a checkout:
  python3 notes/prototypes/closure-register/closure_quant.py > notes/prototypes/closure-register/closure_quant.out
It also writes closure_quant.json beside itself, which check_closures.py reads.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from closure_balls import CAL, TAU, load_calib, radius_where  # noqa: E402

BAR = 0.025                       # the native retention bar of the record
BITS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)


def blocks(c, vec):
    """Each layer as one matrix [W | b]. A relabelling permutes its rows and columns."""
    W1, b1, W2, b2, W3, b3 = c.split(vec)
    return [np.hstack([W1, b1[:, None]]), np.hstack([W2, b2[:, None]]), np.hstack([W3, b3[:, None]])]


def quotient_lower(c, vec, vec0):
    """Mirsky lower bound on the distance from vec0 to any relabelling of vec."""
    total = 0.0
    for a, b in zip(blocks(c, vec), blocks(c, vec0)):
        sa = np.linalg.svd(a, compute_uv=False)
        sb = np.linalg.svd(b, compute_uv=False)
        total += float(np.sum((sa - sb) ** 2))
    return math.sqrt(total)


def relabel(c, vec, p1, p2):
    W1, b1, W2, b2, W3, b3 = c.split(vec)
    parts = [W1[p1], b1[p1], W2[p2][:, p1], b2[p2], W3[:, p2], b3]
    return np.concatenate([a.ravel() for a in parts])


def round_cell(c, vec, bits):
    """Round each weight matrix to 2^bits mid-rise levels. Returns the cell and the steps."""
    out, steps = [], []
    half = 2 ** (bits - 1)
    for a in c.split(vec):
        if a.ndim == 2:
            step = 2.0 * float(np.max(np.abs(a))) / 2 ** bits
            k = np.clip(np.floor(a / step), -half, half - 1)
            out.append((k + 0.5) * step)
            steps.append(step)
        else:
            out.append(a.copy())
    return np.concatenate([a.ravel() for a in out]), steps


def main():
    c = load_calib()
    e13 = c.load_e13()
    gamma = c.gelu_slope_bound()
    res = json.loads((CAL / "results.json").read_text())
    recorded = {h["summary"]["seed"]: h for h in res["hosts"]}
    per_host = {ph["seed"]: ph for ph in res["analysis"]["per_host"]}
    saved = {"tau": TAU, "bar": BAR, "hosts": []}

    print("Part 1. The permutation-quotient ball")
    print("host | fine-tune length | recorded | lower bound on its quotient distance | breaking move length | relabelling test: length, output change, lower bound")
    part2 = []
    for seed in sorted(recorded):
        env = e13.FiveSkillEnvironment(world_seed=c.WORLD0 + seed)
        rng_h = np.random.default_rng(c.HOST0 + seed)
        host = e13.init_organism(rng_h)
        e13.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
        w0 = c.flat_org(host)
        rng_ho = np.random.default_rng(c.HELD0 + seed)
        X_ho, _ = env.sample_batch(rng_ho, [0, 1], 1024, shifted=False)
        X_sh, Y_sh = env.sample_batch(rng_ho, [0, 1], 1024, shifted=True)
        Yho0 = c.forward(w0, X_ho)
        base_r2 = c.r2_e13(w0, X_sh, Y_sh)

        ft_org = c.to_org(e13, w0)
        e13.train_organism_adam(ft_org, env, [0, 1, 2], np.random.default_rng(c.DIR0 + 11 + seed), steps=120)
        wf = c.flat_org(ft_org)
        r_ft = float(np.linalg.norm(wf - w0))
        row = next(x for x in recorded[seed]["rows"] if x["natural"] and x["class"] == "finetune_joint")
        held = c.rms_change(wf, w0, X_ho, Yho0)
        if abs(r_ft - row["r"]) > 1e-9 * row["r"] or abs(held - row["held"]) > 1e-9 * max(1.0, row["held"]):
            raise SystemExit(f"FAIL: rebuilt fine-tune of host {seed} has length {r_ft} and change {held}; the record has {row['r']} and {row['held']}")
        lower = quotient_lower(c, wf, w0)
        if lower > r_ft * (1 + 1e-12):
            raise SystemExit("FAIL: the lower bound exceeds the distance at the identity relabelling")
        brk = per_host[seed]["H6_r_break_adv"]

        # The bound must be blind to a relabelling: a random one moves the weights far,
        # changes no output, and leaves the lower bound at zero.
        rng_p = np.random.default_rng(900 + seed)
        wp = relabel(c, w0, rng_p.permutation(c.M1), rng_p.permutation(c.M2))
        p_len = float(np.linalg.norm(wp - w0))
        p_out = c.rms_change(wp, w0, X_ho, Yho0)
        p_low = quotient_lower(c, wp, w0)
        if p_out > 1e-9 or p_low > 1e-9 or p_len < 1.0:
            raise SystemExit(f"FAIL: relabelling test on host {seed}: length {p_len}, output change {p_out}, lower bound {p_low}")
        print(f"{seed:>4} | {r_ft:>16.4f} | matches  | {lower:>36.4f} | {brk if brk is not None else float('nan'):>20g} | {p_len:.2f}, {p_out:.1e}, {p_low:.1e}")

        h = {"seed": seed, "finetune_r": r_ft, "finetune_quotient_lower": lower, "finetune_joint_pass": bool(row.get("joint_pass")),
             "break_r": brk, "relabel_r": p_len, "relabel_held": p_out, "relabel_quotient_lower": p_low, "bits": []}
        for bits in BITS:
            wq, steps = round_cell(c, w0, bits)
            e = wq - w0
            length = float(np.linalg.norm(e))
            change = c.rms_change(wq, w0, X_ho, Yho0)
            drop = base_r2 - c.r2_e13(wq, X_sh, Y_sh)
            safe = radius_where(lambda q: c.cert_rms(wq, X_ho, q, gamma), TAU)
            h["bits"].append({"bits": bits, "length": length, "held": change, "drop": drop,
                              "min_step": min(steps), "safe_radius": safe})
        part2.append(h)
        saved["hosts"].append(h)

    print("\nPart 2. A rounded copy of the cell (weight matrices rounded to 2^b levels, biases kept)")
    print("bits | length of the rounding error | change on held-out inputs | drop in native score | hosts within tolerance | hosts keeping the bar | "
          "smallest grid step | proved radius at the rounded cell | hosts where a grid step fits the proved ball | hosts where the copy keeps the bar and is longer than the breaking move")
    for i, bits in enumerate(BITS):
        rows = [h["bits"][i] for h in part2]
        rng = lambda k: f"{min(r[k] for r in rows):.4g} to {max(r[k] for r in rows):.4g}"  # noqa: E731
        within = sum(r["held"] <= TAU for r in rows)
        keep = sum(r["drop"] <= BAR for r in rows)
        fits = sum(r["min_step"] <= r["safe_radius"] for r in rows)
        crossed = sum(r["drop"] <= BAR and h["break_r"] is not None and r["length"] > h["break_r"] for r, h in zip(rows, part2))
        print(f"{bits:>4} | {rng('length'):>28} | {rng('held'):>25} | {rng('drop'):>20} | {within:>22} | {keep:>21} | "
              f"{rng('min_step'):>18} | {rng('safe_radius'):>33} | {fits:>44} | {crossed}")
    (HERE / "closure_quant.json").write_text(json.dumps(saved, indent=1) + "\n")


if __name__ == "__main__":
    main()
