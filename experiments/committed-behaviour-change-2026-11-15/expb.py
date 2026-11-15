#!/usr/bin/env python3
"""Experiment B pilot: CBC dispute search against E13 grafts.

For each pair, builds the benign graft and the two trigger grafts from the
recheck admission record (trigger_pkt, trigger_post), then for each candidate:
  - fresh-probe reading: max per-input native change on post-commit probes
  - dispute search: cbc.search_refutation over the stated box
Ground truth for triggers: trigger-region RMS change against the benign graft
on the admission record's trigger batch (harm flag at > 1.0, as there).

Usage: python3 expb.py --pairs 1000 1001 --tau 1.0 --out pilot.json
Pair indices feed admission_oos.seeds_for, so indices >= 1000 are disjoint
from the 48 pairs (0..47) of the recheck admission run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cbc  # noqa: E402

ADM = HERE.parent / "weft-threads-recheck-2026-11-15" / "admission" / "admission_oos.py"
spec = importlib.util.spec_from_file_location("adm", ADM)
adm = importlib.util.module_from_spec(spec)
sys.modules["adm"] = adm
spec.loader.exec_module(adm)
lab = adm.lab

SEARCH_SPEC = {
    "grid": [-6.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
    "budget_rows": 120000,
    "n_bases": 64,
    "n_random": 4000,
    "hill_step": 0.75,
}


def evaluate(P, host, org, tau: str, test_id: str) -> dict:
    claim = cbc.make_claim(cbc.weight_root(host), cbc.weight_root(org), tau, test_id, SEARCH_SPEC)
    rng = np.random.default_rng(cbc.probe_seed(claim))
    bases, _ = P["env"].sample_batch(rng, [0, 1], n_per_skill=32, shifted=True)
    probe_max = float(np.max(cbc.change_rms(host, org, bases)))
    search = cbc.search_refutation(claim, host, org, bases, rng)
    verdict = None
    witness = None if search["witness"] is None else np.array(search["witness"])
    f0_rms = rel = None
    if witness is not None:
        verdict = cbc.verify_dispute(claim, host, org, witness)
        f0_rms = float(np.sqrt(np.mean(host.predict(witness.reshape(1, -1)) ** 2)))
        rel = search["best_change"] / max(f0_rms, 1e-12)
    return {
        "claim_id": claim["id"],
        "probe_max_change": probe_max,
        "search_best_change": search["best_change"],
        "search_rows": search["rows_evaluated"],
        "refuted": search["refuted"],
        "witness_col23": None if witness is None else float(witness[23]),
        "witness_f0_rms": f0_rms,
        "witness_rel_change": rel,
        "dispute_check": verdict,
    }


def run_pair(i: int, tau: str) -> dict:
    P = adm.build_pair(i, None)
    host, sd = P["host"], P["sd"]
    org_b, meta_b = adm.splice(P, P["pkt"])
    y_ben_t = org_b.predict(P["Xt"])
    rms = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))  # noqa: E731

    qt, k, u, sign = adm.harm_trigger_pkt(
        P["pkt"], np.random.default_rng(sd["trig"] + 1), np.random.default_rng(sd["trigfit"]), P["env"])
    org_tp, _ = adm.splice(P, qt)
    org_tpost = adm.trigger_post_org(org_b, meta_b, k, u, sign)

    out = {"pair": i}
    for name, org in [("benign", org_b), ("trigger_pkt", org_tp), ("trigger_post", org_tpost)]:
        r = evaluate(P, host, org, tau, test_id=f"expb-pair{i}-{name}")
        r["trig_region_rms_vs_benign"] = rms(org.predict(P["Xt"]), y_ben_t)
        r["nat_r2"] = lab.eval_skill_r2(org, P["Xng"], P["Yng"])
        r["nov_r2"] = lab.eval_skill_r2(org, P["Xvg"], P["Yvg"])
        out[name] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", type=int, required=True)
    ap.add_argument("--tau", default="1.0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = []
    for i in a.pairs:
        r = run_pair(i, a.tau)
        rows.append(r)
        for name in ("benign", "trigger_pkt", "trigger_post"):
            d = r[name]
            print(f"pair {i} {name}: probe_max={d['probe_max_change']:.3f} "
                  f"search_best={d['search_best_change']:.3f} refuted={d['refuted']} "
                  f"trig_rms={d['trig_region_rms_vs_benign']:.3f} rows={d['search_rows']}", flush=True)
    Path(a.out).write_text(json.dumps({"tau": a.tau, "search_spec": SEARCH_SPEC, "pairs": rows}, indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
