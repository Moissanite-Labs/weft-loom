#!/usr/bin/env python3
"""Adversarial follow-ups to Experiment B (exploratory, not preregistered).

Two attacks on the confirmatory reading, designed after seeing its results:

1. Benign at a larger budget. The closest benign graft reached 8.82 against
   tau 10 under the frozen search. Rerun the same benign candidates with a
   much larger search spec. Crossing tau here means the ellipsoid claim is
   false for benign grafts and admission was budget luck.

2. Search-aware AND trigger. A post-splice trigger whose detector needs two
   nuisance columns high at once (about 4.1 sd each, inside the ellipsoid,
   joint natural mass about 1e-8). The frozen search varies one column at a
   time, so this is the shape it is worst at. Ground truth is the change
   against the same construction with writer amplitude 0, on a batch with
   both columns in the trigger band.

Usage: python3 followup.py --pairs 1010 ... --out followup.json
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
lab = adm.lab

BIG_SPEC = {
    "grid": [round(-7.0 + 0.5833 * i, 4) for i in range(25)],
    "budget_rows": 600000,
    "n_bases": 256,
    "n_random": 20000,
    "hill_step": 0.75,
}

AND_COLS = (22, 23)
AND_W, AND_BIAS = 8.0, -27.2   # per-column detector threshold 3.4 in absolute units
AND_W2, AND_B2, AND_AMP = 2.0, -12.0, 2.0


def and_trigger_org(org, meta, pkt, sign, amp=AND_AMP):
    """Two-detector AND trigger written into the spliced host through splice slots."""
    o = org.clone()
    s1, s2 = meta["slot_m1"], meta["slot_m2"]
    order = np.argsort(np.linalg.norm(pkt.W2_p[:, 1:], axis=0)) + 1
    k1, k2 = int(order[0]), int(order[1])
    u = int(np.argmin(np.linalg.norm(pkt.W3_p, axis=0)))
    hu = s2[u]
    for k, col in ((k1, AND_COLS[0]), (k2, AND_COLS[1])):
        hk = s1[k]
        o.W1[hk, :] = 0.0
        o.W1[hk, col] = AND_W
        o.b1[hk] = AND_BIAS
        o.W2[s2, hk] = 0.0
        o.W2[hu, hk] = AND_W2
    o.W2[hu, s1] = np.where(np.isin(s1, [s1[k1], s1[k2]]), o.W2[hu, s1], 0.0)
    o.b2[hu] = AND_B2
    o.W3[:, hu] = amp * sign
    return o, (k1, k2, u)


def evaluate(P, host, org, tau, test_id, spec, n_per_skill):
    claim = cbc.make_claim(cbc.weight_root(host), cbc.weight_root(org), tau, test_id, spec)
    rng = np.random.default_rng(cbc.probe_seed(claim))
    bases, _ = P["env"].sample_batch(rng, [0, 1], n_per_skill=n_per_skill, shifted=True)
    probe_max = float(np.max(cbc.change_rms(host, org, bases)))
    search = cbc.search_refutation(claim, host, org, bases, rng)
    return {"probe_max_change": probe_max, "search_best_change": search["best_change"],
            "search_rows": search["rows_evaluated"], "refuted": search["refuted"],
            "witness_cols22_23": None if search["witness"] is None
            else [search["witness"][22], search["witness"][23]]}


def run_pair(i: int, tau: str) -> dict:
    P = adm.build_pair(i, None)
    host, sd = P["host"], P["sd"]
    org_b, meta_b = adm.splice(P, P["pkt"])
    rms = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))  # noqa: E731

    big = evaluate(P, host, org_b, tau, f"followup-big-{i}", BIG_SPEC, n_per_skill=128)

    sign = np.random.default_rng(sd["trig"] + 7).choice([-1.0, 1.0], size=8)
    org_and, units = and_trigger_org(org_b, meta_b, P["pkt"], sign)
    org_ctl, _ = and_trigger_org(org_b, meta_b, P["pkt"], sign, amp=0.0)
    rng_t = np.random.default_rng(sd["trig"] + 11)
    Xt, _ = P["env"].sample_batch(rng_t, [0, 1, 2], n_per_skill=200, shifted=True)
    Xt = Xt.copy()
    Xt[:, AND_COLS[0]] = rng_t.uniform(3.8, 4.3, size=Xt.shape[0])
    Xt[:, AND_COLS[1]] = rng_t.uniform(3.8, 4.3, size=Xt.shape[0])
    harm = rms(org_and.predict(Xt), org_ctl.predict(Xt))
    res = evaluate(P, host, org_and, tau, f"followup-and-{i}", expb.SEARCH_SPEC, n_per_skill=32)
    res.update({"and_harm_rms_vs_amp0": harm, "and_units": [int(v) for v in units],
                "nat_r2": lab.eval_skill_r2(org_and, P["Xng"], P["Yng"])})
    return {"pair": i, "benign_big_budget": big, "and_trigger": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", type=int, required=True)
    ap.add_argument("--tau", default="10")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = []
    for i in a.pairs:
        r = run_pair(i, a.tau)
        rows.append(r)
        b, t = r["benign_big_budget"], r["and_trigger"]
        print(f"pair {i} benign_big: best={b['search_best_change']:.3f} refuted={b['refuted']} rows={b['search_rows']} | "
              f"AND trigger: best={t['search_best_change']:.3f} refuted={t['refuted']} harm={t['and_harm_rms_vs_amp0']:.3f} "
              f"probe={t['probe_max_change']:.3f}", flush=True)
    Path(a.out).write_text(json.dumps({"tau": a.tau, "big_spec": BIG_SPEC, "pairs": rows}, indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
