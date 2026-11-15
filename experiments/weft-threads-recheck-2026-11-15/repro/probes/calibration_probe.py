"""Shared-gap calibration probe: does Frobenius weight distance predict behavior change?

Train one E13 host, then compare three moves:
  A. exact hidden-unit permutation (same function, large ||dW||)
  B. random perturbations scaled to graded ||dW||
  C. sign flip of the readout row block (same ||W||, behavior inverted)
Metric: output RMS change on a fresh shifted batch + native R2.
Run: python3 calibration_probe.py
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

PATH = str(Path(__file__).resolve().parents[3] / "e13-geodesic-shunting-plasmid-2026-11-12" / "e13_geodesic_plasmid.py")
spec = importlib.util.spec_from_file_location("e13mod", PATH)
e13 = importlib.util.module_from_spec(spec)
sys.modules["e13mod"] = e13
spec.loader.exec_module(e13)

PARAMS = ["W1", "b1", "W2", "b2", "W3", "b3"]


def flat(org):
    return np.concatenate([getattr(org, p).ravel() for p in PARAMS])


def r2(y_true, y_pred):
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean(axis=0)) ** 2))
    return 1.0 - ss_res / max(ss_tot, 1e-12)


env = e13.FiveSkillEnvironment(world_seed=20261112)
rng = np.random.default_rng(1000)
host = e13.init_organism(rng)
e13.train_organism_adam(host, env, [0, 1], rng, steps=280)

rng_ev = np.random.default_rng(9999)
X, Y = env.sample_batch(rng_ev, [0, 1], 256, shifted=True)
y0 = host.predict(X)
w0 = flat(host)
print(f"host ||W||_F = {np.linalg.norm(w0):.3f}  native shifted R2 = {r2(Y, y0):.4f}")

def report(label, org):
    d = float(np.linalg.norm(flat(org) - w0))
    y = org.predict(X)
    rms = float(np.sqrt(np.mean((y - y0) ** 2)))
    print(f"{label:34s} ||dW||={d:8.3f}  output RMS change={rms:.6f}  native R2={r2(Y, y):.4f}")
    return d, rms

# A: exact symmetry
scr = e13.scramble_organism_hidden_gauge(host, np.random.default_rng(7))
d_perm, _ = report("A permutation (exact symmetry)", scr)

# B: random perturbations at graded scales, 3 draws each
for target in [0.1, 1.0, 5.0, d_perm]:
    rmss = []
    for k in range(3):
        r = np.random.default_rng(100 + k)
        org = host.clone()
        for p in PARAMS:
            cur = getattr(org, p)
            setattr(org, p, cur + r.normal(size=cur.shape))
        d = float(np.linalg.norm(flat(org) - w0))
        scale = target / d
        org2 = host.clone()
        for p in PARAMS:
            setattr(org2, p, getattr(host, p) + (getattr(org, p) - getattr(host, p)) * scale)
        y = org2.predict(X)
        rmss.append(float(np.sqrt(np.mean((y - y0) ** 2))))
    print(f"{'B random ||dW||=' + f'{target:.2f}':34s} output RMS change mean={np.mean(rmss):.6f} (draws {['%.4f' % v for v in rmss]})")

# C: sign flip of readout
flip = host.clone()
flip.W3 = -flip.W3
flip.b3 = -flip.b3
report("C readout sign flip", flip)
