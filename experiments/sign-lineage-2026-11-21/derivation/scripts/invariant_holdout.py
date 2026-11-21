"""Group-invariant lineage statistic (mean over A units of max_j |corr|) with a sampled null:
threshold = maximum over the calibration null pairs; false-positive rate on held-out null pairs;
detection rate on descendants and planted descendants. Width 128 only. Sampled evidence."""
import json, os, sys


def _opt(name, default):
    """Folder option from the command line (for example --out DIR), with the record's layout as default."""
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument(name, default=default)
    known, rest = ap.parse_known_args()
    sys.argv[1:] = rest
    return getattr(known, name.lstrip("-").replace("-", "_"))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = _opt("--out", os.path.join(HERE, "..", "out"))
rows = [json.loads(l) for l in open(os.path.join(OUT, "pairs_all.jsonl"))]
by = {}
for r in rows:
    by.setdefault(r["exp"], []).append(r["inv_mean_maxabs"])
calib = by["null_h128_disjoint"]
thr = max(calib)
held = by["null_other_data_order"] + by["mixed_A_gated_B_gelu"][:0]
res = {"threshold_max_of_200_calibration_null_pairs": thr,
       "heldout_null_other_data_order_fpr": sum(x > thr for x in by["null_other_data_order"]) / len(by["null_other_data_order"]),
       "heldout_null_fixedA_reps_fpr": sum(x > thr for k in ("null_fixedA_gated_rep2", "null_fixedA_gated_rep4", "null_fixedA_gated_rep6", "null_fixedA_gated_rep8") for x in by[k]) / 800,
       "detection": {k: sum(x > thr for x in v) / len(v) for k, v in by.items()
                     if k.startswith(("planted", "descend", "siblings"))},
       "min_value": {k: min(v) for k, v in by.items() if k.startswith(("planted", "descend", "siblings"))}}
with open(os.path.join(OUT, "analysis_zz_invariant.json"), "w") as f:
    json.dump({"invariant_statistic_holdout": res}, f, indent=1, sort_keys=True)
print(json.dumps(res, indent=1, sort_keys=True))
