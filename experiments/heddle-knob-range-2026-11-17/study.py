#!/usr/bin/env python3
"""Heddle knob range: how far can a knob be trusted?

Measures, on small hosts, the things the heddle instrument shows a weaver before a pick and
checks after it. Reads the reference implementation in `notes/prototypes/heddle/heddle.py`.

    python3 study.py --seeds 1 2 3 4 --out pilot.json          (pilot)
    python3 study.py --seeds 101 ... 112 --out results.json    (confirmatory, see PREREG.md)

Two arms per seed:
    random   the host as initialised from the seed
    fitted   the same host after 400 Adam steps towards a striped target picture

Every number is computed in float64 NumPy and is deterministic for a given NumPy build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROTO = HERE.parents[1] / "notes" / "prototypes" / "heddle"
sys.path.insert(0, str(PROTO))
import heddle as hd  # noqa: E402

TAU = 0.5            # the claim's limit, as in the instrument
R_INV = 2.0          # the gate's radius, as in the instrument
SHAFTS = 16
FIT = hd.grid(hd.FIT_GRID)
HELD = hd.grid(31)   # held-out inputs: no coordinate is shared with the 10 x 10 fit grid
TRAVELS = [0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.9, 1.5, 2.5]
PAIRS = [("warm", "tilt"), ("light", "contrast"), ("warm", "light")]
PIN_COUNTS = [1, 4, 16, 32]
KNOWN_GRIDS = [3, 4, 6, 8, 10]
SHARE_FLOOR = 0.2    # a treadle counts for the linearity reading when the shafts carry this much of it


def rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a))))


def fidelity(dy: np.ndarray, pattern: np.ndarray) -> float:
    """Squared cosine between an output change and a pattern: the share of the pattern the
    change carries when it is scaled as well as it can be."""
    return float(np.dot(dy, pattern) ** 2 / (np.dot(dy, dy) * np.dot(pattern, pattern)))


def target_picture(seed: int, pts: np.ndarray) -> np.ndarray:
    """A striped target: one sine wave per output, with small integer frequencies."""
    draw = hd.mulberry32(seed + 1000)
    out = np.zeros((pts.shape[0], hd.M))
    for c in range(hd.M):
        while True:
            kx, ky = int(draw() * 3), int(draw() * 3)
            if kx or ky:
                break
        phase = 2.0 * math.pi * draw()
        out[:, c] = 1.2 * np.sin(2.0 * math.pi * (kx * pts[:, 0] + ky * pts[:, 1]) + phase)
    return out


def fit_host(seed: int, steps: int = 400, lr: float = 0.02) -> tuple[dict, float, float]:
    """Adam on the mean squared error against the target, on a 24 x 24 lattice."""
    pts = hd.grid(24)
    target = target_picture(seed, pts)
    flat = hd.flatten(hd.init_host(seed))
    m, v = np.zeros(hd.P), np.zeros(hd.P)
    first = None
    for t in range(1, steps + 1):
        w = hd.unflatten(flat)
        err = (hd.forward(w, pts) - target).ravel()
        if first is None:
            first = rms(err)
        grad = 2.0 * hd.jacobian(w, pts).T @ err / err.size
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * grad * grad
        flat = flat - lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    w = hd.unflatten(flat)
    return w, first, rms(hd.forward(w, pts) - target)


def measure(arm: str, seed: int) -> dict:
    if arm == "random":
        w, fit_before, fit_after = hd.init_host(seed), None, None
    else:
        w, fit_before, fit_after = fit_host(seed)
    flat = hd.flatten(w)
    root = hd.weight_root(w)
    th = hd.Threading(w, FIT)
    y_fit = hd.forward(w, FIT)
    y_held = hd.forward(w, HELD)
    J_held = hd.jacobian(w, HELD)
    patterns = {n: hd.treadle_pattern(n, FIT, y_fit.ravel()) for n in hd.TREADLE_NAMES}
    held_patterns = {n: hd.treadle_pattern(n, HELD, y_held.ravel()) for n in hd.TREADLE_NAMES}
    tie = hd.TieUp(th, patterns, SHAFTS)
    bound_violations = 0
    bound_checks = 0

    def moved(d: np.ndarray) -> np.ndarray:
        """Output change on the held-out inputs, and a check of the proved bound."""
        nonlocal bound_violations, bound_checks
        dy = hd.forward(hd.unflatten(flat + d), HELD) - y_held
        bound = hd.certified_bound(w, HELD, float(np.linalg.norm(d)))
        bound_checks += 1
        if np.any(np.linalg.norm(dy, axis=1) > bound):
            bound_violations += 1
        return dy.ravel()

    out: dict = {"arm": arm, "seed": seed, "root": root, "fit_rms_before": fit_before, "fit_rms_after": fit_after,
                 "output_rms": rms(y_held), "weight_length": float(np.linalg.norm(flat))}

    # --- the gate's geometry on this host -------------------------------------------------
    lam = th.lam
    out["geometry"] = {
        "lam_max": float(lam[0]), "lam_16": float(lam[15]), "trace": float(np.sum(lam)),
        "kappa": float(math.sqrt(lam[0] * hd.P / np.sum(lam))),
        "silent_dimensions": th.silent_dimensions(),
        "shares": {n: tie.realizable[n] for n in hd.TREADLE_NAMES},
        "unit_throw": {n: float(np.linalg.norm(tie.unit_move[n])) for n in hd.TREADLE_NAMES},
    }

    # --- M1: how far a treadle's label holds ----------------------------------------------
    lin = {}
    for name in hd.TREADLE_NAMES:
        rows = []
        for t in TRAVELS:
            for sign in (1.0, -1.0):
                d = tie.move({name: sign * t})
                dy = moved(d)
                promised = hd.gain_along(th.J @ d, patterns[name])
                measured = hd.gain_along(dy, held_patterns[name])
                first = J_held @ d
                rows.append({"travel": sign * t, "promised": promised, "measured": measured,
                             "ratio": measured / promised if promised else None,
                             "first_order_error": rms(dy - first) / rms(dy)})
        lin[name] = rows
    out["linearity"] = lin

    # --- M2: do two treadles add? ---------------------------------------------------------
    add = []
    for a, b in PAIRS:
        for t in TRAVELS:
            both = moved(tie.move({a: t, b: t}))
            alone = moved(tie.move({a: t})) + moved(tie.move({b: t}))
            add.append({"pair": [a, b], "travel": t, "superposition_error": rms(both - alone) / rms(both)})
    out["additivity"] = add

    # --- M3: heddles ----------------------------------------------------------------------
    generic = tie.move({n: 0.15 for n in hd.TREADLE_NAMES})
    locks = []
    for count in PIN_COUNTS:
        draw = hd.mulberry32(seed * 7 + count)
        pins: list[int] = []
        while len(pins) < count:
            p = int(draw() * hd.PIN_LATTICE * hd.PIN_LATTICE)
            if p not in pins:
                pins.append(p)
        shed = hd.Shed(w, pins)
        pts = hd.pin_points(pins)
        proj = shed.project(generic)
        w_open, w_shed = hd.unflatten(flat + generic), hd.unflatten(flat + proj)
        step = 1.0 / hd.PIN_LATTICE

        def ring(k: int) -> np.ndarray:
            offs = np.array([[k, 0], [-k, 0], [0, k], [0, -k]]) * step
            return np.clip((pts[:, None, :] + offs[None, :, :]).reshape(-1, 2), 0.0, 1.0)

        # Two ways to steer with heddles raised. "projected": push the old 16-shaft move
        # through the shed. "rethreaded": find the 16 shafts of the shed itself and tie the
        # treadles to those (what the instrument does). The share is the fidelity of the
        # output change to the named pattern, a squared cosine; for a tie-up move it equals
        # the realizable share.
        inside = hd.Threading(w, FIT, shed)
        tie_in = hd.TieUp(inside, patterns, SHAFTS)
        shares_projected = {n: fidelity(th.J @ shed.project(tie.unit_move[n]), patterns[n]) for n in hd.TREADLE_NAMES}
        w_re = hd.unflatten(flat + tie_in.move({n: 0.15 for n in hd.TREADLE_NAMES}))
        locks.append({
            "pins": count, "open_dimensions": shed.open_dimensions,
            "shares_projected": shares_projected,
            "shares_rethreaded": {n: tie_in.realizable[n] for n in hd.TREADLE_NAMES},
            "pin_change_rethreaded": float(np.max(hd.change(w, w_re, pts))),
            "near1_change_rethreaded": float(np.max(hd.change(w, w_re, ring(1)))),
            "near4_change_rethreaded": float(np.max(hd.change(w, w_re, ring(4)))),
            "held_change_rethreaded": rms(hd.forward(w_re, HELD) - y_held),
            "kept_length": float(np.linalg.norm(proj) / np.linalg.norm(generic)),
            "pin_change_open": float(np.max(hd.change(w, w_open, pts))),
            "pin_change_shed": float(np.max(hd.change(w, w_shed, pts))),
            "near1_change_open": float(np.max(hd.change(w, w_open, ring(1)))),
            "near1_change_shed": float(np.max(hd.change(w, w_shed, ring(1)))),
            "near4_change_open": float(np.max(hd.change(w, w_open, ring(4)))),
            "near4_change_shed": float(np.max(hd.change(w, w_shed, ring(4)))),
            "held_change_open": rms(hd.forward(w_open, HELD) - y_held),
            "held_change_shed": rms(hd.forward(w_shed, HELD) - y_held),
        })
    out["locks"] = locks

    # --- M4: hiding from known probes -----------------------------------------------------
    hide = []
    for g in KNOWN_GRIDS:
        known = hd.grid(g)
        d = hd.hidden_move(w, known, hd.grid(24), 0.3)
        w1 = hd.unflatten(flat + d)
        cid = hd.claim_id(root, hd.weight_root(w1), str(TAU), [])
        fresh = hd.fresh_probes(hd.weight_root(w1), cid, 64)
        worst, _, _ = hd.dispute_search(w, w1)
        hide.append({
            "known_grid": g, "known_rows": g * g * hd.M,
            "on_known": hd.behaviour_change(w, w1, known),
            "elsewhere": hd.behaviour_change(w, w1, HELD),
            "fresh_rms": hd.behaviour_change(w, w1, fresh),
            "fresh_max": float(np.max(hd.change(w, w1, fresh))),
            "worst": worst,
        })
    out["hiding"] = hide

    # --- M5: ball against behaviour -------------------------------------------------------
    rng = np.random.default_rng(seed)
    at_radius = []
    for _ in range(20):
        d = rng.standard_normal(hd.P)
        d *= R_INV / np.linalg.norm(d)
        moved(d)
        at_radius.append(hd.dispute_search(w, hd.unflatten(flat + d))[0])

    def worst_along_top(r: float) -> float:
        return float(np.max(hd.change(w, hd.unflatten(flat + r * th.V[:, 0]), hd.grid(48))))

    lo, hi = 0.0, R_INV
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if worst_along_top(mid) > TAU:
            hi = mid
        else:
            lo = mid
    limit = TAU * math.sqrt(hd.M)
    clo, chi = 0.0, 1.0
    for _ in range(60):
        mid = 0.5 * (clo + chi)
        if float(np.max(hd.certified_bound(w, HELD, mid))) <= limit:
            clo = mid
        else:
            chi = mid
    out["ball"] = {
        "random_at_radius_worst": at_radius,
        "random_at_radius_refuted": int(sum(v > TAU for v in at_radius)),
        "top_shaft_breaking_radius": hi,
        "certified_radius": clo,
        "first_order_radius": TAU / math.sqrt(float(lam[0])),
    }

    # --- M7: does tension forecast the check? ---------------------------------------------
    draw = hd.mulberry32(seed * 13 + 5)
    forecast = []
    for _ in range(60):
        k = 1 + int(draw() * 3)
        names = []
        while len(names) < k:
            n = hd.TREADLE_NAMES[int(draw() * len(hd.TREADLE_NAMES))]
            if n not in names:
                names.append(n)
        d = tie.move({n: (2.0 * draw() - 1.0) * 0.6 for n in names})
        moved(d)
        tension = max(float(np.linalg.norm(d)) / R_INV, hd.predicted_worst(th.J, d) / TAU)
        worst, _, _ = hd.dispute_search(w, hd.unflatten(flat + d))
        forecast.append({"tension": tension, "worst": worst, "snap": bool(worst > TAU)})
    out["forecast"] = forecast

    out["bound"] = {"checks": bound_checks, "violations": bound_violations}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--arms", nargs="+", default=["random", "fitted"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    hosts = []
    for arm in args.arms:
        for seed in args.seeds:
            hosts.append(measure(arm, seed))
            print(f"{arm} {seed} done", flush=True)
    doc = {
        "schema": "heddle-knob-range/1",
        "constants": {"tau": TAU, "r_invariant": R_INV, "shafts": SHAFTS, "travels": TRAVELS,
                      "pin_counts": PIN_COUNTS, "known_grids": KNOWN_GRIDS, "share_floor": SHARE_FLOOR},
        "programs": {"study.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                     "heddle.py": hashlib.sha256((PROTO / "heddle.py").read_bytes()).hexdigest()},
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "machine": platform.machine(), "system": platform.system()},
        "hosts": hosts,
    }
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
