#!/usr/bin/env python3
"""Turn a results file of calib.py or calib_tf.py into the numbers the README cites.

Writes <name>.summary.json and prints a Markdown summary. Every number in the
README comes from the summary file, and the claims ledger of the recheck
record checks the sentences against it.

Usage:
  python3 summarise.py results.json
  python3 summarise.py results_tf.json
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

TAU = 0.05


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def rng(xs):
    xs = [x for x in xs if x is not None]
    return [min(xs), max(xs)] if xs else None


def sig(x, n=3):
    if x is None or isinstance(x, bool) or not isinstance(x, float):
        return x
    if x == 0.0 or not math.isfinite(x):
        return x
    return float(f"{x:.{n}g}")


def verdict(count, n):
    if count is None:
        return "not tested"
    if count >= n - 1 and n >= 12:
        return "confirmed"
    if count <= n // 2:
        return "refuted"
    return "mixed"


def safe_size(rows, cls, tau):
    """Largest radius with held change at most tau, interpolated on log scales.

    For classes with several draws the worst draw at each radius is used.
    Returns None if even the smallest tested radius exceeds tau, and the
    largest tested radius if tau is never reached.
    """
    pts = {}
    for x in rows:
        if x["class"] == cls and not x["natural"]:
            pts[x["r"]] = max(pts.get(x["r"], 0.0), x["held"])
    rs = sorted(pts)
    if not rs:
        return None
    if pts[rs[0]] > tau:
        return None
    for lo, hi in zip(rs, rs[1:]):
        if pts[lo] <= tau < pts[hi]:
            if pts[lo] <= 0.0:
                return lo
            f = (math.log(tau) - math.log(pts[lo])) / (math.log(pts[hi]) - math.log(pts[lo]))
            return math.exp(math.log(lo) + f * (math.log(hi) - math.log(lo)))
    return rs[-1]


def main():
    path = Path(sys.argv[1])
    res = json.loads(path.read_text())
    hosts = res["hosts"]
    an = res["analysis"]
    n = an["n_hosts"]
    tests = an["tests"]
    r_loc, r_blind = tests["r_loc"], tests["r_blind"]
    out = {
        "source": path.name,
        "program_sha256": res["program_sha256"],
        "n_hosts": n,
        "seeds": res["seeds"],
        "r_loc": r_loc,
        "r_blind": r_blind,
        "tau": TAU,
        "counts": {k: v for k, v in tests.items() if k.startswith("H")},
        "verdicts": {k: verdict(v, n) for k, v in tests.items() if k.startswith("H")},
    }

    S = [h["summary"] for h in hosts]
    P = an["per_host"]
    for key in ("weight_norm", "sqrt_lam_max", "sqrt_mean_lam", "anisotropy", "effective_rank"):
        out[key + "_median"] = sig(med([s[key] for s in S]))
        out[key + "_range"] = [sig(v) for v in rng([s[key] for s in S])]
    out["n_weights"] = S[0]["n_weights"]
    out["drop_metric"] = S[0]["drop_metric"]
    scale_key = "output_rms_shift" if "output_rms_shift" in S[0] else "output_rms_held"
    out["output_rms_median"] = sig(med([s[scale_key] for s in S]))

    classes = sorted({x["class"] for h in hosts for x in h["rows"] if not x["natural"]})
    out["breaking_radius"] = {}
    out["safe_size_tau"] = {}
    for c in classes:
        br = [s["r_break"].get(c) for s in S]
        out["breaking_radius"][c] = {
            "median": med(br), "range": rng(br), "hosts_never_broken": sum(1 for v in br if v is None)}
        ss = [safe_size(h["rows"], c, TAU) for h in hosts]
        out["safe_size_tau"][c] = {"median": sig(med(ss)), "range": [sig(v) for v in rng(ss)] if rng(ss) else None}

    nat = sorted({x["class"] for h in hosts for x in h["rows"] if x["natural"]})
    out["natural_moves"] = {}
    for c in nat:
        rows = [next(x for x in h["rows"] if x["natural"] and x["class"] == c) for h in hosts]
        d = {k: sig(med([x[k] for x in rows])) for k in ("r", "fisher", "probe", "held", "drop")}
        d["r_range"] = [sig(v) for v in rng([x["r"] for x in rows])]
        d["held_max"] = sig(max(x["held"] for x in rows))
        d["drop_max"] = sig(max(x["drop"] for x in rows))
        if "joint_pass" in rows[0]:
            d["joint_pass"] = sum(1 for x in rows if x["joint_pass"])
        out["natural_moves"][c] = d

    def at(h, cls, r):
        return [x for x in h["rows"] if x["class"] == cls and not x["natural"] and abs(x["r"] - r) <= 1e-9 * max(1.0, r)]

    # Null moves: first-order leak onto held-out inputs, and second-order change on the probes.
    leak = [statistics.mean(x["held"] for x in at(h, "null", r_loc)) / r_loc for h in hosts]
    randl = [statistics.mean(x["held"] for x in at(h, "rand", r_loc)) / r_loc for h in hosts]
    out["null_leak_per_unit_median"] = sig(med(leak))
    out["rand_change_per_unit_median"] = sig(med(randl))
    out["null_leak_over_rand_median"] = sig(med([a / b for a, b in zip(leak, randl)]))
    r2 = 10.0 * r_loc
    c2 = [statistics.mean(x["probe"] for x in at(h, "null", r2)) / r2 ** 2 for h in hosts]
    out["null_second_order_coeff_median"] = sig(med(c2))
    out["null_second_order_radius"] = r2

    out["top_over_rand_median"] = sig(med([p["H1_top_over_rand"] for p in P]))
    out["top_over_rand_range"] = [sig(v) for v in rng([p["H1_top_over_rand"] for p in P])]
    out["top_held_over_probe_range"] = [sig(v) for v in rng([p["top_held_over_probe"] for p in P])]
    out["H2_probe_over_fisher_range"] = [sig(min(p["H2_probe_over_fisher_min"] for p in P), 4),
                                         sig(max(p["H2_probe_over_fisher_max"] for p in P), 4)]
    out["H2_held_over_fisher_range"] = [sig(min(p["H2_held_over_fisher_min"] for p in P), 4),
                                        sig(max(p["H2_held_over_fisher_max"] for p in P), 4)]
    out["H4_held_over_probe_range"] = [sig(min(p["H4_held_over_probe_min"] for p in P), 4),
                                       sig(max(p["H4_held_over_probe_max"] for p in P), 4)]
    out["H5_blind_ratio_median"] = sig(med([p["H5_blind_ratio"] for p in P]))
    out["H5_blind_ratio_range"] = [sig(v) for v in rng([p["H5_blind_ratio"] for p in P])]
    out["H5_blind_held_median"] = sig(med([p["H5_blind_held"] for p in P]))
    out["H5_blind_probe_median"] = sig(med([p["H5_blind_probe"] for p in P]))
    out["one_step_r_median"] = sig(med([p["H6_one_step_r"] for p in P]))
    out["r_break_adv_values"] = sorted({p["H6_r_break_adv"] for p in P if p["H6_r_break_adv"] is not None})
    out["r_break_rand_values"] = sorted({p["H6_r_break_rand"] for p in P if p["H6_r_break_rand"] is not None})
    if "H5_blind_under_graft_drop" in P[0]:
        out["H5b_drop_median"] = sig(med([p["H5_blind_under_graft_drop"] for p in P]))
        out["H5b_radius_values"] = sorted({p["H5_blind_under_graft_r"] for p in P if p["H5_blind_under_graft_r"] is not None})
        out["graft_probe_median"] = sig(med([p["H6_graft_probe"] for p in P]))
    if "H7_cert_radius_0p05" in P[0]:
        out["cert_radius_median"] = sig(med([p["H7_cert_radius_0p05"] for p in P]))
        out["attack_radius_values"] = sorted({p["H7_attack_radius_0p05"] for p in P if p["H7_attack_radius_0p05"] is not None})
        out["first_order_radius_median"] = sig(med([s["first_order_radius_tau_0p05"] for s in S]))
        out["first_order_over_cert_median"] = sig(med(
            [s["first_order_radius_tau_0p05"] / s["cert_radius_tau_0p05"] for s in S]))

    dst = path.with_name(path.stem + ".summary.json")
    dst.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    print(f"## {path.name}: {n} hosts, {out['n_weights']} weights\n")
    print("| Prediction | Hosts on which it holds | Verdict |")
    print("|---|---|---|")
    for k, v in out["counts"].items():
        print(f"| {k} | {'not tested' if v is None else f'{v} of {n}'} | {out['verdicts'][k]} |")
    print(f"\n| Class of move | Breaking radius, median (range) | Safe size at change {TAU}, median |")
    print("|---|---|---|")
    for c in classes:
        b = out["breaking_radius"][c]
        rtxt = "never broken" if b["median"] is None else f"{b['median']:g} ({b['range'][0]:g} to {b['range'][1]:g})"
        if b["hosts_never_broken"] and b["median"] is not None:
            rtxt += f", {b['hosts_never_broken']} hosts never broken"
        s = out["safe_size_tau"][c]["median"]
        print(f"| {c} | {rtxt} | {'below the grid' if s is None else f'{s:g}'} |")
    print("\n| Move at its own length | Distance | Fisher prediction | Change on probes | Change held-out | Drop |")
    print("|---|---|---|---|---|---|")
    for c in nat:
        d = out["natural_moves"][c]
        extra = f", passes {d['joint_pass']} of {n}" if "joint_pass" in d else ""
        print(f"| {c} | {d['r']:g} | {d['fisher']:g} | {d['probe']:g} | {d['held']:g} | {d['drop']:g}{extra} |")
    print(f"\nwrote {dst.name}")


if __name__ == "__main__":
    main()
