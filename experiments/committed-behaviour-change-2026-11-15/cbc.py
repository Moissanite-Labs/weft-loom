#!/usr/bin/env python3
"""Committed Behaviour Change v0: weight roots, claims, probe order, dispute.

Implements DESIGN.md in this folder for the E13 harness organisms
(numpy MLPs with named tensors W1, b1, W2, b2, W3, b3 and a predict method).
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction

import numpy as np

DOMAIN = b"WEFT-CBC-V1:"
TENSOR_NAMES = ["W1", "b1", "W2", "b2", "W3", "b3"]
BOX_LO, BOX_HI = -8.0, 8.0
GATE_COLS = list(range(16, 21))
FREE_COLS = list(range(0, 16)) + [21, 22, 23]
NATIVE_GATES = (0, 1)
MIN_NATIVE_GATE = 1.5
# Shifted native sampler of the E13 environment, per free column.
MU = np.array([0.25] * 16 + [-0.30] * 3)
SIGMA = np.array([1.30] * 16 + [0.85] * 3)
ELLIPSOID_R2 = 64.0


def _standardized(X: np.ndarray) -> np.ndarray:
    return (X[..., FREE_COLS] - MU) / SIGMA


def project_in_domain(X: np.ndarray) -> np.ndarray:
    """Clip to the sanity box and scale standardized free coords into the ellipsoid."""
    X = np.clip(np.array(X, dtype=np.float64, copy=True), BOX_LO, BOX_HI)
    z = _standardized(X)
    r2 = np.sum(z * z, axis=-1)
    over = r2 > ELLIPSOID_R2
    if np.any(over):
        scale = np.sqrt(ELLIPSOID_R2 / np.maximum(r2, 1e-12))
        z = np.where(over[..., None], z * scale[..., None], z)
        X[..., FREE_COLS] = MU + z * SIGMA
    return X


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tensor_leaf(name: str, arr: np.ndarray) -> str:
    a = np.asarray(arr)
    le = a.astype(a.dtype.newbyteorder("<"), copy=False)
    header = _canonical_json({"name": name, "shape": list(a.shape), "dtype": a.dtype.str})
    return hashlib.sha256(DOMAIN + b"leaf:" + header + b":" + np.ascontiguousarray(le).tobytes()).hexdigest()


def weight_root(tensors) -> str:
    """Root hash of a dict of named tensors, or an organism with tensor attributes."""
    if not isinstance(tensors, dict):
        tensors = {n: getattr(tensors, n) for n in TENSOR_NAMES}
    h = hashlib.sha256(DOMAIN + b"root:")
    for name in sorted(tensors):
        h.update(name.encode() + b":" + tensor_leaf(name, tensors[name]).encode() + b";")
    return h.hexdigest()


def change_rms(f0, f1, X: np.ndarray) -> np.ndarray:
    """Per-input RMS output change between two organisms."""
    d = f1.predict(X) - f0.predict(X)
    return np.sqrt(np.mean(d * d, axis=1))


def in_domain(x: np.ndarray) -> bool:
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.shape != (24,) or not np.all(np.isfinite(x)):
        return False
    if np.any(x < BOX_LO) or np.any(x > BOX_HI):
        return False
    if float(np.sum(_standardized(x) ** 2)) > ELLIPSOID_R2:
        return False
    gates = x[GATE_COLS]
    g = int(np.argmax(gates))
    return g in NATIVE_GATES and gates[g] >= MIN_NATIVE_GATE


def make_claim(w0_root: str, w1_root: str, tau: str, test_id: str, search_spec: dict) -> dict:
    claim = {
        "schema": "cbc/1",
        "w0_root": w0_root,
        "w1_root": w1_root,
        "claim": {
            "kind": "native_retention_ellipsoid",
            "tau": tau,
            "box": [BOX_LO, BOX_HI],
            "ellipsoid_r2": ELLIPSOID_R2,
            "mu": [float(v) for v in MU],
            "sigma": [float(v) for v in SIGMA],
            "native_gates": list(NATIVE_GATES),
            "min_native_gate": MIN_NATIVE_GATE,
        },
        "probe_spec": {"test_id": test_id, "derivation": "sha256(domain|test_id|w1_root|claim_id)"},
        "search_spec": search_spec,
    }
    claim["id"] = hashlib.sha256(DOMAIN + b"claim:" + _canonical_json(claim)).hexdigest()
    return claim


def probe_seed(claim: dict) -> int:
    h = hashlib.sha256(
        DOMAIN + b"probes:" + claim["probe_spec"]["test_id"].encode() + b"|"
        + claim["w1_root"].encode() + b"|" + claim["id"].encode()
    ).digest()
    return int.from_bytes(h[:8], "little")


def verify_dispute(claim: dict, f0, f1, x: np.ndarray) -> dict:
    """One-input refutation check. Returns the verdict and the measured change."""
    if weight_root(f0) != claim["w0_root"] or weight_root(f1) != claim["w1_root"]:
        return {"refuted": False, "reason": "weight_root_mismatch", "change": None}
    if not in_domain(x):
        return {"refuted": False, "reason": "outside_domain", "change": None}
    change = float(change_rms(f0, f1, np.asarray(x, dtype=np.float64).reshape(1, -1))[0])
    tau = Fraction(claim["claim"]["tau"])
    return {"refuted": bool(Fraction(change).limit_denominator(10**12) > tau),
            "reason": "predicate_violated" if change > float(tau) else "within_tolerance",
            "change": change}


def search_refutation(claim: dict, f0, f1, base_rows: np.ndarray, rng: np.random.Generator) -> dict:
    """Bounded search for a dispute input. Budget comes from claim['search_spec'].

    Stages: coordinate sweep over free columns, random perturbation, hill climb.
    Returns the best input found, its change, rows evaluated, and the verdict.
    """
    spec = claim["search_spec"]
    tau = float(Fraction(claim["claim"]["tau"]))
    grid = np.array(spec["grid"], dtype=np.float64)
    budget = int(spec["budget_rows"])
    evaluated = 0
    best_x, best_c = None, -1.0

    def consider(X):
        nonlocal evaluated, best_x, best_c
        X = project_in_domain(np.atleast_2d(np.asarray(X, dtype=np.float64)))
        room = budget - evaluated
        if room <= 0:
            return False
        X = X[:room]
        evaluated += X.shape[0]
        c = change_rms(f0, f1, X)
        i = int(np.argmax(c))
        if c[i] > best_c:
            best_c, best_x = float(c[i]), X[i].copy()
        return best_c > tau

    bases = np.asarray(base_rows, dtype=np.float64)[: int(spec["n_bases"])]
    if consider(bases):
        return _result(claim, best_x, best_c, evaluated)
    # coordinate sweep; grid values are in standardized (sigma) units
    for j, col in enumerate(FREE_COLS):
        cand = np.repeat(bases, len(grid), axis=0)
        cand[:, col] = np.tile(MU[j] + grid * SIGMA[j], len(bases))
        if consider(cand):
            return _result(claim, best_x, best_c, evaluated)
    # random perturbation inside the box (non-gate columns only)
    n_rand = int(spec["n_random"])
    if n_rand > 0:
        idx = rng.integers(0, len(bases), size=n_rand)
        cand = bases[idx].copy()
        cand[:, FREE_COLS] = MU + rng.normal(0.0, 2.0, size=(n_rand, len(FREE_COLS))) * SIGMA
        if consider(cand):
            return _result(claim, best_x, best_c, evaluated)
    # hill climb on free columns from the best point found
    step = float(spec["hill_step"])
    improved = True
    while improved and evaluated < budget:
        improved = False
        for col in FREE_COLS:
            for delta in (step, -step):
                x = best_x.copy()
                x[col] = min(BOX_HI, max(BOX_LO, x[col] + delta))
                before = best_c
                if consider(x.reshape(1, -1)):
                    return _result(claim, best_x, best_c, evaluated)
                if best_c > before:
                    improved = True
        step *= 0.5
        if step < 1e-3:
            break
    return _result(claim, best_x, best_c, evaluated)


def _result(claim, best_x, best_c, evaluated):
    tau = float(Fraction(claim["claim"]["tau"]))
    return {
        "refuted": bool(best_c > tau),
        "best_change": float(best_c),
        "rows_evaluated": int(evaluated),
        "witness": None if best_x is None else [float(v) for v in best_x],
    }
