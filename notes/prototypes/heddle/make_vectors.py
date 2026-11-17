#!/usr/bin/env python3
"""Write `vectors.json`: values computed by the reference (`heddle.py`) that the JavaScript
mirror (`heddle.js`) must reproduce. Run from this folder:  python3 make_vectors.py

Exact entries (hashes, generator draws, probe coordinates) must match bit for bit. Numeric
entries carry the tolerance the JavaScript test applies; they differ only through the last
digits of tanh and sin, and through block iteration against an exact SVD.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import heddle as hd

HERE = Path(__file__).resolve().parent
SEED = 7
PINS = [100, 2000, 3000]


def test_move() -> np.ndarray:
    """A fixed move built from integers only, so both languages hold the same bytes."""
    return np.array([(((i * 37) % 101) - 50) / 50.0 for i in range(hd.P)]) * 0.01


def main() -> None:
    draw = hd.mulberry32(12345)
    w = hd.init_host(SEED)
    flat = hd.flatten(w)
    fit = hd.grid(hd.FIT_GRID)
    pts = np.array([[0.1, 0.2], [0.5, 0.5], [0.9, 0.05], [0.33, 0.77], [0.0, 1.0]])
    d = test_move()
    th = hd.Threading(w, fit)
    y = hd.forward(w, fit)
    patterns = {n: hd.treadle_pattern(n, fit, y.ravel()) for n in hd.TREADLE_NAMES}
    tie = hd.TieUp(th, patterns, 16)
    shed = hd.Shed(w, PINS)
    proj = shed.project(d)
    th_shed = hd.Threading(w, fit, shed)
    tie_shed = hd.TieUp(th_shed, patterns, 16)
    w1 = hd.unflatten(flat + d)
    root0, root1 = hd.weight_root(w), hd.weight_root(w1)
    cid = hd.claim_id(root0, root1, "0.5", PINS)
    probes = hd.fresh_probes(root1, cid, 8)
    big = hd.unflatten(flat + th.shaft_move(0, 0.4))
    worst, witness, rows = hd.dispute_search(w, big)
    known = hd.grid(4)
    hidden = hd.hidden_move(w, known, hd.grid(24), 0.5)
    wh = hd.unflatten(flat + hidden)
    Jd = hd.jacobian(w, pts) @ d

    out = {
        "schema": "heddle-vectors/1",
        "note": "Written by make_vectors.py from heddle.py. Do not edit by hand.",
        "seed": SEED,
        "pins": PINS,
        "exact": {
            "mulberry32_12345": [draw() for _ in range(8)],
            "weights_head": flat[:6].tolist(),
            "weights_tail": flat[-3:].tolist(),
            "w0_root": root0,
            "w1_root": root1,
            "claim_id": cid,
            "fresh_probes": probes.tolist(),
            "event_id": hd.event_id({"seq": 1, "kind": "pick", "prev": "genesis", "parent_root": root0,
                                     "root": root1, "move_sha256": "00" * 32, "pins": PINS,
                                     "gesture": "hold", "tau": "0.5"}),
            "silent_dimensions": th.silent_dimensions(),
            "open_dimensions": shed.open_dimensions,
        },
        "numeric": {
            "forward": {"points": pts.tolist(), "outputs": hd.forward(w, pts).tolist(), "atol": 1e-12},
            "jacobian_times_move": {"values": Jd.tolist(), "atol": 1e-12},
            "eigenvalues_16": {"values": th.lam[:16].tolist(), "rtol": 1e-8},
            "predicted_change": {"value": th.predicted_change(d), "rtol": 1e-10},
            "realizable_16": {"values": tie.realizable, "atol": 1e-7},
            "unit_move_length_16": {"values": {k: float(np.linalg.norm(v)) for k, v in tie.unit_move.items()},
                                    "rtol": 1e-6},
            "projected_move_length": {"value": float(np.linalg.norm(proj)), "rtol": 1e-10},
            "pin_leak_first_order": {"value": float(np.max(np.abs(shed.J @ proj))), "atol": 1e-12},
            "eigenvalues_16_in_shed": {"values": th_shed.lam[:16].tolist(), "rtol": 1e-8},
            "realizable_16_in_shed": {"values": tie_shed.realizable, "atol": 1e-7},
            "certified_bound_r03": {"values": hd.certified_bound(w, pts, 0.3).tolist(), "rtol": 1e-10},
            "behaviour_change": {"value": hd.behaviour_change(w, w1, fit), "rtol": 1e-9},
            "dispute": {"worst": worst, "witness": list(witness), "rows": rows, "rtol": 1e-6},
            "hidden_move": {
                "radius": 0.5,
                "known_grid": 4,
                "elsewhere_grid": 24,
                "change_on_probes": hd.behaviour_change(w, wh, known),
                "change_elsewhere": hd.behaviour_change(w, wh, hd.grid(24)),
                "rtol": 1e-4,
            },
        },
    }
    (HERE / "vectors.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("wrote vectors.json")


if __name__ == "__main__":
    main()
