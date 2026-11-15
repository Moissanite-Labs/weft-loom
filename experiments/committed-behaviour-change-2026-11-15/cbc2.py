#!/usr/bin/env python3
"""Committed Behaviour Change v2: lessons of Experiment A and B applied.

Changes against v1 (cbc.py, frozen at its preregistration hash):
  - Weight roots are over canonical float32 tensors. Cross-host reading:
    float64 roots disagree even where float32 weights are identical.
  - The record carries the discrete decisions made at splice time (slot
    lists) and the packet wire hash. Replay consumes them. Recomputing
    decisions from seeds is retraining, not replay.
  - A domain guard: inputs outside the claimed ellipsoid are flagged, and
    the claim says nothing about them. V1 had no guard.
Dispute recomputation casts weights to float32 first, then computes in
float64, so the verified object is the one the root names.
"""
from __future__ import annotations

import copy
import hashlib
import json
from fractions import Fraction

import numpy as np

import cbc

DOMAIN2 = b"WEFT-CBC-V2:"


def f32_root(org) -> str:
    """Root over canonical float32 tensors of an organism or tensor dict."""
    tensors = org if isinstance(org, dict) else {n: getattr(org, n) for n in cbc.TENSOR_NAMES}
    h = hashlib.sha256(DOMAIN2 + b"root:")
    for name in sorted(tensors):
        a = np.asarray(tensors[name], dtype=np.float32)
        header = json.dumps({"name": name, "shape": list(a.shape), "dtype": a.dtype.str},
                            sort_keys=True, separators=(",", ":")).encode()
        leaf = hashlib.sha256(DOMAIN2 + b"leaf:" + header + b":" + np.ascontiguousarray(a).tobytes()).hexdigest()
        h.update(name.encode() + b":" + leaf.encode() + b";")
    return h.hexdigest()


def as_f32(org):
    """Copy of an organism with every tensor cast to float32 (the rooted object)."""
    out = copy.copy(org)
    for n in cbc.TENSOR_NAMES:
        setattr(out, n, np.asarray(getattr(org, n), dtype=np.float32))
    return out


def guard(x: np.ndarray) -> str:
    """Runtime domain guard: the claim speaks only inside the ellipsoid."""
    return "in_domain" if cbc.in_domain(x) else "out_of_domain"


def make_claim_v2(w0, w1, tau: str, test_id: str, search_spec: dict,
                  packet_sha256: str, decisions: dict) -> dict:
    claim = {
        "schema": "cbc/2",
        "w0_root": f32_root(w0),
        "w1_root": f32_root(w1),
        "claim": {
            "kind": "native_retention_ellipsoid",
            "tau": tau,
            "box": [cbc.BOX_LO, cbc.BOX_HI],
            "ellipsoid_r2": cbc.ELLIPSOID_R2,
            "mu": [float(v) for v in cbc.MU],
            "sigma": [float(v) for v in cbc.SIGMA],
            "native_gates": list(cbc.NATIVE_GATES),
            "min_native_gate": cbc.MIN_NATIVE_GATE,
        },
        "artifacts": {"packet_sha256": packet_sha256, "decisions": decisions},
        "probe_spec": {"test_id": test_id, "derivation": "sha256(domain2|test_id|w1_root|claim_id)"},
        "search_spec": search_spec,
    }
    body = json.dumps(claim, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    claim["id"] = hashlib.sha256(DOMAIN2 + b"claim:" + body).hexdigest()
    return claim


def probe_seed_v2(claim: dict) -> int:
    h = hashlib.sha256(
        DOMAIN2 + b"probes:" + claim["probe_spec"]["test_id"].encode() + b"|"
        + claim["w1_root"].encode() + b"|" + claim["id"].encode()
    ).digest()
    return int.from_bytes(h[:8], "little")


def verify_dispute_v2(claim: dict, f0, f1, x: np.ndarray) -> dict:
    if f32_root(f0) != claim["w0_root"] or f32_root(f1) != claim["w1_root"]:
        return {"refuted": False, "reason": "weight_root_mismatch", "change": None}
    if guard(x) != "in_domain":
        return {"refuted": False, "reason": "outside_domain", "change": None}
    change = float(cbc.change_rms(as_f32(f0), as_f32(f1),
                                  np.asarray(x, dtype=np.float64).reshape(1, -1))[0])
    tau = Fraction(claim["claim"]["tau"])
    over = Fraction(change).limit_denominator(10**12) > tau
    return {"refuted": bool(over),
            "reason": "predicate_violated" if over else "within_tolerance",
            "change": change}
