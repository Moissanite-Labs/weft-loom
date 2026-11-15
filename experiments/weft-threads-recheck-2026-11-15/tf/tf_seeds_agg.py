"""Aggregate tf_seeds.py outputs: pass counts with Clopper-Pearson 95% intervals, per-skill means, gate counts."""
import json
import sys
import numpy as np
from tf_common import clopper_pearson, die


def load(prefix):
    rows = []
    for suf in ("a", "b"):
        try:
            rows += json.load(open(f"{prefix}_{suf}.json"))
        except FileNotFoundError:
            die("missing " + prefix + suf)
    return sorted(rows, key=lambda r: r["seed"])


def main(out):
    res = {}
    lines = []
    for mode in ("std", "ho"):
        rows = load(f"seeds_{mode}")
        n = len(rows)
        seeds = [r["seed"] for r in rows]
        if len(set(seeds)) != n:
            die("duplicate seeds")
        lines.append(f"\n=== mode {mode}: n={n} seeds {seeds[0]}..{seeds[-1]} ===")
        lines.append("host/donor ref (mean over seeds, 'in' test set): host " +
                     str([round(np.mean([r['arms']['host']['acc']['in'][t] for r in rows]), 4) for t in ('0', '1', '2')]) +
                     " donor task2 " + str(round(np.mean([r['donor_task2']['in']['2'] for r in rows]), 4)))
        names = list(rows[0]["arms"].keys())
        res[mode] = {}
        for tset in ("in", "ho"):
            lines.append(f"\n-- test set '{tset}' (mode {mode}) --")
            lines.append(f"{'arm':22s} {'pass':>6s} {'CP95':>16s}  mean acc COPY/ADD3/MUL5      min COPY/ADD3/MUL5    dist(mean) g10 g120")
            for a in names:
                accs = np.array([[r["arms"][a]["acc"][tset][t] for t in ("0", "1", "2")] for r in rows])
                row = {"mean": accs.mean(0).round(4).tolist(), "min": accs.min(0).round(4).tolist(),
                       "per_seed": accs.tolist()}
                s = ""
                if a != "host":
                    k = sum(r["arms"][a]["pass_" + tset] for r in rows)
                    lo, hi = clopper_pearson(k, n)
                    row.update(pass_count=k, n=n, cp95=[lo, hi])
                    s = f"{k:3d}/{n:<2d} [{lo:.3f},{hi:.3f}]"
                dd = ""
                if "frob_dist" in rows[0]["arms"].get(a, {}):
                    d = np.array([r["arms"][a]["frob_dist"] for r in rows])
                    g10 = sum(r["arms"][a]["gate10"] for r in rows)
                    g120 = sum(r["arms"][a]["gate120"] for r in rows)
                    row.update(frob_mean=float(d.mean()), frob_min=float(d.min()), frob_max=float(d.max()), gate10=g10, gate120=g120)
                    dd = f"{d.mean():7.2f} {g10:2d}/{n} {g120:2d}/{n}"
                lines.append(f"{a:22s} {s:>24s}  {accs.mean(0).round(3)}  {accs.min(0).round(3)}  {dd}")
                res[mode].setdefault(tset, {})[a] = row
        ov = [r["overlap"] for r in rows]
        lines.append("overlap in-test tuples seen in training stream (mean unique/inTrain): " +
                     str((np.mean([o['in']['n_unique_test_tuples'] for o in ov]), np.mean([o['in']['n_in_training_stream'] for o in ov]))) +
                     "; held-out: " + str((np.mean([o['ho']['n_unique_test_tuples'] for o in ov]), np.mean([o['ho']['n_in_training_stream'] for o in ov]))))
        ld = [r["arms"]["pres_true_dorm"]["max_abs_logit_diff_vs_external"] for r in rows]
        lines.append(f"max |logit(spliced) - logit(external)| pres_true_dorm: mean {np.mean(ld):.4f} max {np.max(ld):.4f}")
        lines.append("secs/seed mean " + str(round(np.mean([r['secs'] for r in rows]), 1)))
        lines.append("per-seed pres_true_dorm / pres_donor_dorm / pres_*_rand passes (in): " + str([(r['seed'],
                     int(r['arms']['pres_true_dorm']['pass_in']), int(r['arms']['pres_donor_dorm']['pass_in']),
                     int(r['arms']['pres_true_rand']['pass_in']), int(r['arms']['pres_donor_rand']['pass_in'])) for r in rows]))
        res[mode]["seeds"] = seeds
    print("\n".join(lines))
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
