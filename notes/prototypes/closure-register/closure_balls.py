#!/usr/bin/env python3
"""How large a ball of moves does one failed move close? (fact 4 of the note)

For a host of the calibration record, rebuild the adversary's move at each
tested length, check it against the recorded row, and apply Theorem 1 at the
moved weights. Every move within rho of a move d* whose change on the held-out
inputs is D* changes behaviour by at least D* - B(rho), where B(rho) is the
proved bound taken at w0 + d*. The closed radius is the largest rho with
B(rho) < D* - tau. The same bound around the baseline gives the ball of moves
proved safe.

Needs NumPy. Usage, from the root of a checkout:
  python3 notes/prototypes/closure-register/closure_balls.py > notes/prototypes/closure-register/closure_balls.out
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "experiments" / "gate-metric-calibration-2026-11-15"
TAU = 0.05   # tolerance on the RMS change over the held-out inputs, as in H7 of the record


def load_calib():
    spec = importlib.util.spec_from_file_location("calib", CAL / "calib.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["calib"] = mod
    spec.loader.exec_module(mod)
    return mod


def radius_where(bound, target):
    """Largest rho with bound(rho) < target, for an increasing bound. Zero if there is none."""
    if target <= 0.0:
        return 0.0
    lo, hi = 0.0, 1e-6
    while bound(hi) < target:
        lo, hi = hi, hi * 2.0
        if hi > 1e6:
            return math.inf
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if bound(mid) < target else (lo, mid)
    return lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(12)))
    a = ap.parse_args()
    c = load_calib()
    e13 = c.load_e13()
    gamma = c.gelu_slope_bound()
    recorded = {h["summary"]["seed"]: h for h in json.loads((CAL / "results.json").read_text())["hosts"]}
    print(f"tolerance tau = {TAU} on the RMS change over 2048 held-out inputs (1024 per skill); slope bound gamma = {gamma:.4f}")
    for seed in a.seeds:
        # The same construction as run_host in calib.py, as far as the adversary's moves.
        env = e13.FiveSkillEnvironment(world_seed=c.WORLD0 + seed)
        rng_h = np.random.default_rng(c.HOST0 + seed)
        host = e13.init_organism(rng_h)
        e13.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
        w0 = c.flat_org(host)
        env.sample_batch(np.random.default_rng(c.FIT0 + seed), [0, 1], 128, shifted=False)
        X_ho, _ = env.sample_batch(np.random.default_rng(c.HELD0 + seed), [0, 1], 1024, shifted=False)
        X_att, _ = env.sample_batch(np.random.default_rng(c.ATT0 + seed), [0, 1], 128, shifted=False)
        Yho0 = c.forward(w0, X_ho)
        J_att = c.jacobian(w0, X_att)
        _, U_a = np.linalg.eigh(J_att @ J_att.T / (X_att.shape[0] * c.D_OUT))
        top_att = c.unit(J_att.T @ U_a[:, -1])
        safe = radius_where(lambda rho: c.cert_rms(w0, X_ho, rho, gamma), TAU)
        one_step = next(x["r"] for x in recorded[seed]["rows"] if x["natural"] and x["class"] == "one_step")
        print(f"\nhost {seed}: weight norm {np.linalg.norm(w0):.2f}; ball proved safe around the baseline: radius {safe:.5f}; one training step has length {one_step:.3f}")
        print("   length of failed move | its change D* | recorded | closed radius rho* | rho* / length | rho* / one step | least change on edge | (D*/tau - 1) x safe radius")
        for r in (0.03, 0.1, 0.3, 1.0, 3.0):
            d = c.pga(w0, X_att, r, top_att, steps=80)
            w = w0 + d
            D = c.rms_change(w, w0, X_ho, Yho0)
            rec = next(x["held"] for x in recorded[seed]["rows"] if x["class"] == "adv" and not x["natural"] and abs(x["r"] - r) < 1e-12)
            if abs(D - rec) > 1e-9 * max(1.0, rec):
                raise SystemExit(f"FAIL: rebuilt move at length {r} gives change {D}, the record has {rec}")
            rho = radius_where(lambda q: c.cert_rms(w, X_ho, q, gamma), D - TAU)
            # The theorem needs no test, but the program is checked: moves on the edge of the closed ball
            # must stay over the tolerance. Tried: straight back toward the baseline, down the gradient
            # of the change, and 20 random directions.
            g = c.vjp(w, X_ho, 2.0 * (c.forward(w, X_ho) - Yho0) / Yho0.size)
            rng = np.random.default_rng(1000 + seed)
            tries = [-c.unit(d), -c.unit(g)] + [c.unit(rng.normal(size=c.P)) for _ in range(20)]
            low = min(c.rms_change(w + rho * u, w0, X_ho, Yho0) for u in tries)
            if rho > 0 and low < TAU:
                raise SystemExit(f"FAIL: a move inside the closed ball at length {r} is under the tolerance")
            first = radius_where(lambda q: c.cert_rms(w0, X_ho, q, gamma), TAU) * (D / TAU - 1.0)
            print(f"   {r:>21g} | {D:>13.4f} | matches  | {rho:>18.5f} | {rho / r:>13.4f} | {rho / one_step:>15.5f} | {low:>21.4f} | {first:>10.5f}")


if __name__ == "__main__":
    main()
