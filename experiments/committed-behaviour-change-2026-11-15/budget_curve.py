#!/usr/bin/env python3
"""Exploratory budget-sensitivity curve for benign CBC claims.

Designed after the confirmatory and follow-up readings. For each benign graft
from the confirmatory pairs, run one nested escalating candidate stream and
record the largest in-domain native change found at fixed evaluated-row
checkpoints. This measures how the apparent safety margin at tau changes as a
disputant gets more search budget. It is not the frozen Experiment B search:
the candidate stream is denser and checkpoints are recorded within the stream.

Stages: post-commit bases, one-coordinate sweep, repeated random blocks, with
a bounded hill climb after each random block. Every candidate is projected
into the v1 ellipsoid before evaluation. The search stops at the first row
whose change exceeds tau, or at the maximum budget.

Usage:
  python3 budget_curve.py --pairs 1010 ... --tau 10 --max-budget 600000 \
      --out budget-curve.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cbc  # noqa: E402
import expb  # noqa: E402

adm = expb.adm

CHECKPOINTS = [256, 1000, 5000, 19036, 50000, 100000, 142236, 300000, 600000]
GRID = np.array([round(-7.0 + 0.5833 * i, 4) for i in range(25)], dtype=np.float64)
RANDOM_BLOCK = 10000
HILL_STEPS = [0.75 * (0.5**i) for i in range(10)]


class SearchTrace:
    def __init__(self, f0, f1, tau: float, max_budget: int):
        self.f0 = f0
        self.f1 = f1
        self.tau = float(tau)
        self.max_budget = int(max_budget)
        self.evaluated = 0
        self.best_change = -1.0
        self.best_x = None
        self.crossing_row = None
        self.checkpoints = []
        self._next_checkpoint = 0

    @property
    def done(self) -> bool:
        return self.crossing_row is not None or self.evaluated >= self.max_budget

    def _record_checkpoints(self, changes: np.ndarray, X: np.ndarray, start_row: int) -> None:
        total = start_row + len(changes)
        running_best = self.best_change
        while self._next_checkpoint < len(CHECKPOINTS):
            target = CHECKPOINTS[self._next_checkpoint]
            if target > total or target > self.max_budget:
                break
            take = target - start_row
            if take > 0:
                running_best = max(running_best, float(np.max(changes[:take])))
            self.checkpoints.append({"rows": int(target), "best_change": float(running_best)})
            self._next_checkpoint += 1

    def consider(self, X) -> bool:
        """Evaluate candidates, updating checkpoints and stopping at tau crossing."""
        if self.done:
            return True
        X = cbc.project_in_domain(np.atleast_2d(np.asarray(X, dtype=np.float64)))
        room = self.max_budget - self.evaluated
        if room <= 0:
            return True
        X = X[:room]
        start = self.evaluated
        changes = cbc.change_rms(self.f0, self.f1, X)

        crossing = np.flatnonzero(changes > self.tau)
        if len(crossing):
            idx = int(crossing[0])
            self._record_checkpoints(changes[: idx + 1], X[: idx + 1], start)
            self.evaluated = start + idx + 1
            self.best_change = float(changes[idx])
            self.best_x = X[idx].copy()
            self.crossing_row = int(self.evaluated)
            return True

        self._record_checkpoints(changes, X, start)

        idx = int(np.argmax(changes))
        if float(changes[idx]) > self.best_change:
            self.best_change = float(changes[idx])
            self.best_x = X[idx].copy()
        self.evaluated = start + len(changes)
        return self.done


def hill_climb(trace: SearchTrace) -> None:
    for step in HILL_STEPS:
        improved = True
        while improved and not trace.done:
            improved = False
            for col in cbc.FREE_COLS:
                for delta in (step, -step):
                    if trace.done or trace.best_x is None:
                        return
                    x = trace.best_x.copy()
                    x[col] = min(cbc.BOX_HI, max(cbc.BOX_LO, x[col] + delta))
                    before = trace.best_change
                    trace.consider(x.reshape(1, -1))
                    if trace.best_change > before:
                        improved = True


def run_curve(P, host, org, tau: str, pair: int, max_budget: int) -> dict:
    spec = {
        "protocol": "nested_bases_sweep_random_hill",
        "grid": [float(v) for v in GRID],
        "budget_rows": int(max_budget),
        "n_bases": 256,
        "n_random_block": RANDOM_BLOCK,
        "hill_steps": HILL_STEPS,
        "checkpoints": CHECKPOINTS,
    }
    claim = cbc.make_claim(
        cbc.weight_root(host), cbc.weight_root(org), tau,
        f"budget-curve-{pair}", spec,
    )
    rng = np.random.default_rng(cbc.probe_seed(claim))
    bases, _ = P["env"].sample_batch(rng, [0, 1], n_per_skill=128, shifted=True)
    trace = SearchTrace(host, org, float(tau), max_budget)

    trace.consider(bases)
    sweep_bases = bases[:64]
    for j, col in enumerate(cbc.FREE_COLS):
        if trace.done:
            break
        cand = np.repeat(sweep_bases, len(GRID), axis=0)
        cand[:, col] = np.tile(cbc.MU[j] + GRID * cbc.SIGMA[j], len(sweep_bases))
        trace.consider(cand)

    while not trace.done:
        idx = rng.integers(0, len(bases), size=RANDOM_BLOCK)
        cand = bases[idx].copy()
        cand[:, cbc.FREE_COLS] = (
            cbc.MU + rng.normal(0.0, 2.0, size=(RANDOM_BLOCK, len(cbc.FREE_COLS))) * cbc.SIGMA
        )
        trace.consider(cand)
        hill_climb(trace)

    return {
        "pair": pair,
        "claim_id": claim["id"],
        "tau": float(tau),
        "max_budget": int(max_budget),
        "rows_evaluated": int(trace.evaluated),
        "best_change": float(trace.best_change),
        "crossed_tau": trace.crossing_row is not None,
        "crossing_row": trace.crossing_row,
        "checkpoints": trace.checkpoints,
        "witness": None if trace.best_x is None else [float(v) for v in trace.best_x],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", type=int, required=True)
    ap.add_argument("--tau", default="10")
    ap.add_argument("--max-budget", type=int, default=600000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    for i in a.pairs:
        P = adm.build_pair(i, None)
        org_b, _ = adm.splice(P, P["pkt"])
        row = run_curve(P, P["host"], org_b, a.tau, i, a.max_budget)
        rows.append(row)
        marks = " ".join(f"{c['rows']}:{c['best_change']:.2f}" for c in row["checkpoints"])
        print(
            f"pair {i} crossed={row['crossed_tau']} crossing_row={row['crossing_row']} "
            f"best={row['best_change']:.3f} rows={row['rows_evaluated']} | {marks}",
            flush=True,
        )

    out = {
        "kind": "exploratory_budget_sensitivity",
        "designed_after_confirmatory": True,
        "tau": a.tau,
        "max_budget": a.max_budget,
        "checkpoints": CHECKPOINTS,
        "pairs": rows,
    }
    Path(a.out).write_text(json.dumps(out, indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
