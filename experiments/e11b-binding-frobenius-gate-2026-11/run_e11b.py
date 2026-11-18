#!/usr/bin/env python3
"""E11b: binding Frobenius-gate sweep on toy horizontal transfer.

CPU-only NumPy. Harness aligned with Moissanite-Labs/weft PR #201 (prereg-faithful E11).

  python3 experiments/e11b-binding-frobenius-gate-2026-11/run_e11b.py
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

HERE = Path(__file__).resolve().parent


def _repo_root() -> Path:
    for base in (HERE, *HERE.parents):
        if (base / ".git").is_dir():
            return base
    return HERE.parents[2]

PREREG_SEEDS = [17, 29, 43, 101, 202]
R_FRACTIONS = [0.1, 0.25, 0.5, 0.75, 1.0]
CORE_HIDDEN = 4
D_IN = 8
HIDDEN = 16
N_TASKS = 4
N_KEPT = 3
NEW_TASK = N_KEPT
N_EVAL = 512
TRAIN_STEPS_KEPT = 800
TRAIN_STEPS_NEW = 500
LR = 0.08
RETENTION_TOL = 0.10
NEW_TASK_ACC_BAR = 0.80
SHIFTED_PASS_NEED = 3
RAW_MATCH_ATOL = 1e-12


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(_repo_root()), "rev-parse", "HEAD"]
        ).decode().strip()
    except Exception:
        return "unknown"


@dataclass
class ToyParams:
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray

    def clone(self) -> "ToyParams":
        return ToyParams(self.w1.copy(), self.b1.copy(), self.w2.copy(), self.b2.copy())

    def plastic_mask(self) -> np.ndarray:
        mask = np.ones(self.flat().size, dtype=np.float64)
        mask[: CORE_HIDDEN * D_IN] = 0.0
        off = self.w1.size
        mask[off : off + CORE_HIDDEN] = 0.0
        return mask

    def flat(self) -> np.ndarray:
        return np.concatenate([self.w1.ravel(), self.b1, self.w2.ravel(), self.b2])

    @staticmethod
    def from_flat(flat: np.ndarray) -> "ToyParams":
        off = 0
        w1 = flat[off : off + HIDDEN * D_IN].reshape(HIDDEN, D_IN)
        off += HIDDEN * D_IN
        b1 = flat[off : off + HIDDEN]
        off += HIDDEN
        w2 = flat[off : off + N_TASKS * HIDDEN].reshape(N_TASKS, HIDDEN)
        off += N_TASKS * HIDDEN
        b2 = flat[off : off + N_TASKS]
        return ToyParams(w1, b1, w2, b2)


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def init_params(seed: int) -> ToyParams:
    g = rng(seed)
    return ToyParams(
        g.normal(0, 0.4, (HIDDEN, D_IN)),
        np.zeros(HIDDEN),
        g.normal(0, 0.4, (N_TASKS, HIDDEN)),
        np.zeros(N_TASKS),
    )


def task_hyperplanes(seed: int) -> Tuple[np.ndarray, np.ndarray]:
    g = rng(seed + 9000)
    w = g.normal(0, 1, (N_TASKS, D_IN))
    w /= np.linalg.norm(w, axis=1, keepdims=True) + 1e-9
    b = g.normal(0, 0.1, N_TASKS)
    return w, b


def labels_for(x: np.ndarray, tw: np.ndarray, tb: np.ndarray, task: int) -> np.ndarray:
    return np.sign(x @ tw[task] + tb[task])


def forward(p: ToyParams, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    z1 = x @ p.w1.T + p.b1
    h = np.maximum(0.0, z1)
    pre_logits = h @ p.w2.T + p.b2
    return h, np.tanh(pre_logits)


def accuracy(p: ToyParams, x: np.ndarray, tw: np.ndarray, tb: np.ndarray, task: int) -> float:
    _, logits = forward(p, x)
    return float(np.mean(np.sign(logits[:, task]) == labels_for(x, tw, tb, task)))


def backward_task(
    p: ToyParams, x: np.ndarray, tw: np.ndarray, tb: np.ndarray, task_ids: Sequence[int]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = x.shape[0]
    z1 = x @ p.w1.T + p.b1
    h = np.maximum(0.0, z1)
    pre_logits = h @ p.w2.T + p.b2
    logits = np.tanh(pre_logits)
    dtanh = 1.0 - logits**2
    dz2 = np.zeros_like(logits)
    for t in task_ids:
        y = labels_for(x, tw, tb, t)
        dz2[:, t] = 2.0 * (logits[:, t] - y) / n * dtanh[:, t]
    dw2 = dz2.T @ h
    db2 = np.sum(dz2, axis=0)
    dh = dz2 @ p.w2
    dh[z1 <= 0.0] = 0.0
    return dh.T @ x, np.sum(dh, axis=0), dw2, db2


def train_tasks(
    p: ToyParams,
    mask: np.ndarray,
    x: np.ndarray,
    tw: np.ndarray,
    tb: np.ndarray,
    task_ids: Sequence[int],
    steps: int,
) -> ToyParams:
    flat = p.flat().copy()
    idx = np.where(mask > 0.5)[0]
    for _ in range(steps):
        cur = ToyParams.from_flat(flat)
        dw1, db1, dw2, db2 = backward_task(cur, x, tw, tb, task_ids)
        grad = np.concatenate([dw1.ravel(), db1, dw2.ravel(), db2])
        flat[idx] -= LR * grad[idx]
    return ToyParams.from_flat(flat)


def sample_uniform(n: int, seed: int) -> np.ndarray:
    return rng(seed).uniform(-1.0, 1.0, (n, D_IN))


ROTATE = np.linalg.qr(rng(7).normal(0, 1, (D_IN, D_IN)))[0]
PROBE_NAMES = ["iid", "scale_1p5", "shift_pos", "rotate", "sparse"]
SHIFTED_NAMES = ["scale_1p5", "shift_pos", "rotate", "sparse"]
PROBE_NAME_OFFSET = {name: int(zlib.crc32(name.encode()) % 10_000) for name in PROBE_NAMES}


def apply_probe(name: str, x: np.ndarray) -> np.ndarray:
    if name == "iid":
        return x
    if name == "scale_1p5":
        return 1.5 * x
    if name == "shift_pos":
        return x + 0.3
    if name == "rotate":
        return x @ ROTATE.T
    if name == "sparse":
        z = x.copy()
        z[:, 4:] = 0.0
        return z
    raise ValueError(name)


def grad_logit_wrt_plastic(p: ToyParams, mask: np.ndarray, x_row: np.ndarray, task: int) -> np.ndarray:
    flat = p.flat()
    idx = np.where(mask > 0.5)[0]
    eps = 1e-4
    base_logit = forward(p, x_row[None, :])[1][0, task]
    rows = []
    for i in idx:
        pert = flat.copy()
        pert[i] += eps
        rows.append((forward(ToyParams.from_flat(pert), x_row[None, :])[1][0, task] - base_logit) / eps)
    return np.array(rows, dtype=np.float64)


def plastic_vec_from_delta(delta: ToyParams, mask: np.ndarray) -> np.ndarray:
    return delta.flat()[mask > 0.5]


def params_delta(a: ToyParams, b: ToyParams) -> ToyParams:
    return ToyParams(a.w1 - b.w1, a.b1 - b.b1, a.w2 - b.w2, a.b2 - b.b2)


def apply_plastic_delta(p: ToyParams, mask: np.ndarray, d_plastic: np.ndarray) -> ToyParams:
    flat = p.flat().copy()
    flat[mask > 0.5] += d_plastic
    return ToyParams.from_flat(flat)


def frobenius_clip(d: np.ndarray, radius: float) -> Tuple[np.ndarray, bool, float]:
    n = float(np.linalg.norm(d))
    if n <= radius or n == 0.0:
        return d.copy(), False, n
    clipped = d * (radius / n)
    return clipped, True, float(np.linalg.norm(clipped))


def eval_retention(
    pre: ToyParams, post: ToyParams, tw: np.ndarray, tb: np.ndarray, probe_seed: int
) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for pname in PROBE_NAMES:
        x = apply_probe(pname, sample_uniform(N_EVAL, probe_seed + PROBE_NAME_OFFSET[pname]))
        row: Dict[str, float] = {}
        for t in range(N_KEPT):
            a0 = accuracy(pre, x, tw, tb, t)
            a1 = accuracy(post, x, tw, tb, t)
            row[f"task{t}_drop"] = a0 - a1
            row[f"task{t}_pass"] = 1.0 if a0 - a1 <= RETENTION_TOL else 0.0
        out[pname] = row
    return out


def shifted_probe_pass_count(ret: Dict[str, Dict[str, float]]) -> int:
    return sum(
        1
        for pname in SHIFTED_NAMES
        if all(ret[pname][f"task{t}_pass"] >= 1.0 for t in range(N_KEPT))
    )


def linearization_error(
    pre: ToyParams, post: ToyParams, mask: np.ndarray, x: np.ndarray, task: int
) -> float:
    d = plastic_vec_from_delta(params_delta(post, pre), mask)
    errs = []
    for i in range(min(64, x.shape[0])):
        pred = float(grad_logit_wrt_plastic(pre, mask, x[i], task) @ d)
        actual = forward(post, x[i : i + 1])[1][0, task] - forward(pre, x[i : i + 1])[1][0, task]
        errs.append(abs(pred - actual))
    return float(np.mean(errs)) if errs else float("nan")


def eval_arm(
    pre_b: ToyParams,
    post: ToyParams,
    tw: np.ndarray,
    tb: np.ndarray,
    mask: np.ndarray,
    seed: int,
) -> Dict:
    x_new = sample_uniform(N_EVAL, seed + 5000)
    ret = eval_retention(pre_b, post, tw, tb, seed + 7000)
    return {
        "new_task_accuracy": accuracy(post, x_new, tw, tb, NEW_TASK),
        "iid_all_kept_pass": all(ret["iid"][f"task{t}_pass"] >= 1.0 for t in range(N_KEPT)),
        "shifted_probe_pass_count": shifted_probe_pass_count(ret),
        "retention_by_probe": ret,
        "nonlinear_drift_new_task_mae": linearization_error(pre_b, post, mask, x_new[:64], NEW_TASK),
        "training_steps_b": 0,
    }


def run_seed(seed: int) -> Dict:
    tw, tb = task_hyperplanes(seed)
    x_train = sample_uniform(600, seed + 10000)
    mask = init_params(0).plastic_mask()

    p_a = train_tasks(init_params(seed), mask, x_train, tw, tb, list(range(N_KEPT)), TRAIN_STEPS_KEPT)
    base_a = p_a.clone()
    p_a = train_tasks(p_a, mask, x_train, tw, tb, [NEW_TASK], TRAIN_STEPS_NEW)
    p_b = train_tasks(init_params(seed + 1000), mask, x_train, tw, tb, list(range(N_KEPT)), TRAIN_STEPS_KEPT)
    pre_b = p_b.clone()

    d_plastic = plastic_vec_from_delta(params_delta(p_a, base_a), mask)
    d_fro = float(np.linalg.norm(d_plastic))

    raw_post = apply_plastic_delta(p_b, mask, d_plastic.copy())
    raw_metrics = eval_arm(pre_b, raw_post, tw, tb, mask, seed)

    by_fraction: Dict[str, Dict] = {}
    for frac in R_FRACTIONS:
        r_gate = frac * d_fro
        clipped, clip_bound, post_norm = frobenius_clip(d_plastic, r_gate)
        post = apply_plastic_delta(p_b, mask, clipped)
        metrics = eval_arm(pre_b, post, tw, tb, mask, seed)
        metrics.update(
            {
                "r_fraction": frac,
                "r_gate": r_gate,
                "clip_bound": clip_bound,
                "post_clip_norm": post_norm,
                "delta_frobenius_plastic": d_fro,
            }
        )
        by_fraction[f"f{frac:g}"] = metrics

    return {
        "seed": seed,
        "mode": "cross_seed",
        "delta_frobenius_plastic": d_fro,
        "raw_coord": raw_metrics,
        "frobenius_by_fraction": by_fraction,
    }


def aggregate_fraction(runs: List[Dict], key: str) -> Dict:
    acc, sh, iid = [], [], []
    clip_any = []
    post_norms = []
    for r in runs:
        arm = r["raw_coord"] if key == "raw_coord" else r["frobenius_by_fraction"][key]
        acc.append(arm["new_task_accuracy"])
        sh.append(arm["shifted_probe_pass_count"])
        iid.append(1.0 if arm["iid_all_kept_pass"] else 0.0)
        if key != "raw_coord":
            clip_any.append(1.0 if arm["clip_bound"] else 0.0)
            post_norms.append(arm["post_clip_norm"])
    out = {
        "new_task_accuracy_mean": float(np.mean(acc)),
        "new_task_accuracy_std": float(np.std(acc, ddof=1)) if len(acc) > 1 else 0.0,
        "new_task_accuracy_per_seed": acc,
        "shifted_pass_mean": float(np.mean(sh)),
        "shifted_pass_per_seed": sh,
        "iid_retention_rate": float(np.mean(iid)),
        "bar_new_task_080": float(np.mean(acc)) >= NEW_TASK_ACC_BAR,
        "bar_shifted_3of4": float(np.mean(sh)) >= SHIFTED_PASS_NEED,
        "bar_iid_1p0": float(np.mean(iid)) >= 1.0,
    }
    if key != "raw_coord":
        out["clip_bound_rate"] = float(np.mean(clip_any))
        out["post_clip_norm_mean"] = float(np.mean(post_norms))
    return out


def sanity_checks(runs: List[Dict]) -> Dict:
    f1_matches = []
    norm_monotone = []
    for r in runs:
        raw = r["raw_coord"]
        f1 = r["frobenius_by_fraction"]["f1"]
        match = (
            abs(f1["new_task_accuracy"] - raw["new_task_accuracy"]) <= RAW_MATCH_ATOL
            and f1["shifted_probe_pass_count"] == raw["shifted_probe_pass_count"]
            and not f1["clip_bound"]
            and abs(f1["post_clip_norm"] - r["delta_frobenius_plastic"]) <= 1e-9
        )
        f1_matches.append(match)
        norms = [r["frobenius_by_fraction"][f"f{frac:g}"]["post_clip_norm"] for frac in R_FRACTIONS]
        norm_monotone.append(all(norms[i] <= norms[i + 1] + 1e-9 for i in range(len(norms) - 1)))
    return {
        "f1_matches_raw_coord_every_seed": all(f1_matches),
        "post_clip_norm_nondecreasing_in_f_every_seed": all(norm_monotone),
        "per_seed_f1_match": f1_matches,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "results" / "e11b_results.json")
    args = parser.parse_args()
    t0 = time.perf_counter()
    runs = [run_seed(s) for s in PREREG_SEEDS]
    agg = {"raw_coord": aggregate_fraction(runs, "raw_coord")}
    for frac in R_FRACTIONS:
        agg[f"f{frac:g}"] = aggregate_fraction(runs, f"f{frac:g}")
    payload = {
        "experiment": "E11b",
        "parent": "E11",
        "weft_reference": "https://github.com/Moissanite-Labs/weft/pull/201",
        "prereg": "PREREG.md",
        "commit": git_commit(),
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "seeds_cross": PREREG_SEEDS,
        "r_fractions": R_FRACTIONS,
        "per_seed_cross": runs,
        "aggregate_cross_seed": agg,
        "sanity_checks": sanity_checks(runs),
        "constants": {
            "RETENTION_TOL": RETENTION_TOL,
            "NEW_TASK_ACC_BAR": NEW_TASK_ACC_BAR,
            "SHIFTED_PASS_NEED": SHIFTED_PASS_NEED,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {args.out}")
    print(f"Sanity f1≡raw: {payload['sanity_checks']['f1_matches_raw_coord_every_seed']}")


if __name__ == "__main__":
    main()