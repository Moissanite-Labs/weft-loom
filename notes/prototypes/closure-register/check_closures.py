#!/usr/bin/env python3
"""Check the closure register against the committed data.

A sector of paths is closed only by a certificate: two bounds on one
parameter that cross, or one exhibited counterexample to a universal claim.
This program checks every certificate in closures.json against the numbers
saved under experiments/, prints the two bounds for each unit, and exits
with status 1 if a registered closure does not hold on a unit it claims. It
then closes every path that needs something closed, and repeats until
nothing changes.

It reads recorded numbers and does not rebuild the moves behind them. The
programs that produced them are in the records named below and are
deterministic for a given seed. closure_balls.py rebuilds the adversary's
moves on the MLP hosts and checks them against the record. closure_quant.py
rebuilds the fine-tunes of the MLP hosts and saves closure_quant.json, which
CL-5 to CL-7 read. closure_persist.py does the same for CL-8 and saves
closure_persist.json. The breaking move and the fine-tune behind CL-5, CL-6
and CL-8 are checked against the calibration record. The numbers of the rounded cells
exist only in closure_quant.json and are read as saved. What a path needs is
written by hand in closures.json.

Usage: python3 notes/prototypes/closure-register/check_closures.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAL = ROOT / "experiments" / "gate-metric-calibration-2026-11-15"
RECHECK = ROOT / "experiments" / "weft-threads-recheck-2026-11-15"
BAR = 0.025          # a larger drop breaks the bar: R2 on shifted native data (MLP), accuracy on held-out native inputs (transformer)
NOVEL_MIN = 0.70     # the joint bar also asks this much on the new skill
TAU = 0.05           # tolerance of CL-1, as a share of the output RMS
SILENT = 1e-9        # a permutation changes no output beyond rounding


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def plasm_linear_cell():
    """CL-1. Upper bound from the exact worst case of a linear map, lower bound from the recorded drift."""
    p = load(CAL / "plasm_radius.json")
    per_unit = p["smax_stimuli"] / math.sqrt(p["n_stimuli"] * p["dim"])
    if abs(per_unit - p["worst_rms_change_per_unit_distance"]) > 1e-12 * per_unit:
        raise SystemExit("FAIL: the worst case per unit distance does not match smax / sqrt(n d)")
    upper = TAU * p["output_rms"] / per_unit
    lower = p["paper1_max_drift"]
    tau_star = lower * per_unit / p["output_rms"]
    note = f"bounds meet at tau_star = {tau_star:.4f}; at the shipped radius {p['shipped_radius']:g} the worst case is {p['shipped_radius'] * per_unit / p['output_rms']:.1f} times the output RMS"
    return [dict(unit="Plasm cell, 16 stimuli", upper=upper, lower=lower, closed=upper < lower, note=note)]


def ball_gate_nonlinear():
    """CL-2. An exhibited breaking move shorter than an exhibited fine-tune that passes."""
    out = []
    for name, label in (("results.json", "MLP"), ("results_tf.json", "transformer")):
        res = load(CAL / name)
        for host, ph in zip(res["hosts"], res["analysis"]["per_host"]):
            rows = host["rows"]
            upper = ph["H6_r_break_adv"]
            harm = [x for x in rows if x["class"] == "adv" and not x["natural"] and upper is not None and abs(x["r"] - upper) <= 1e-12]
            fine = next(x for x in rows if x["natural"] and x["class"] == "finetune_joint")
            perm = next(x for x in rows if x["natural"] and x["class"] == "perm")
            if not harm:
                out.append(dict(unit=f"{label} host {ph['seed']}", upper=None, lower=fine["r"], closed=False, note="no breaking move recorded"))
                continue
            novel = fine.get("novel_r2_after", fine.get("novel_acc_after"))
            ok = harm[0]["drop"] > BAR and fine["drop"] <= BAR and novel >= NOVEL_MIN and upper <= fine["r"]
            silent = perm["held"] <= SILENT and upper <= perm["r"]
            note = (f"breaking move drops {harm[0]['drop']:.4f}; fine-tune drops {fine['drop']:.4f}; "
                    f"a permutation of length {perm['r']:.1f} changes outputs by {perm['held']:.1e}" + ("" if silent else " (NOT silent)"))
            out.append(dict(unit=f"{label} host {ph['seed']}", upper=upper, lower=fine["r"], closed=ok and silent, note=note))
    return out


def probe_threshold_known_probes():
    """CL-3. A move built to hide from the probes shows less probe change than a graft that passes, and breaks the bar."""
    out = []
    res = load(CAL / "results.json")
    for host, ph in zip(res["hosts"], res["analysis"]["per_host"]):
        rows = host["rows"]
        graft = next(x for x in rows if x["natural"] and x["class"] == "graft")
        r_blind = ph["H5_blind_under_graft_r"]
        blind = [x for x in rows if x["class"] == "adv_blind" and r_blind is not None and abs(x["r"] - r_blind) <= 1e-12]
        if not ph["H6_graft_joint_pass"]:
            out.append(dict(unit=f"MLP host {ph['seed']}", upper=None, lower=graft["probe"], closed=None,
                            note="the graft fails the joint bar here, so there is no benign witness and nothing is certified"))
            continue
        ok = (bool(blind) and blind[0]["drop"] > BAR and blind[0]["probe"] <= graft["probe"]
              and graft["drop"] <= BAR and graft["novel_r2_after"] >= NOVEL_MIN)
        out.append(dict(unit=f"MLP host {ph['seed']}", upper=blind[0]["probe"] if blind else None, lower=graft["probe"], closed=ok,
                        note=f"hidden move of length {r_blind:g} drops {blind[0]['drop']:.3f}; graft drops {graft['drop']:.4f}" if blind else "no hidden move recorded"))
    return out


def admission_rule_sufficient():
    """CL-4. Grafts the frozen rule admits although they fail the joint bar."""
    rows = load(RECHECK / "admission" / "admission_oos.json")["rows"]
    bad = [r for r in rows if r["admit"] and not r["gt_pass"]]
    trig = [r for r in rows if r["admit"] and r["trig_harm"]]
    by = {}
    for r in bad:
        by[r["cls"]] = by.get(r["cls"], 0) + 1
    note = f"{len(bad)} of {sum(1 for r in rows if r['admit'])} admitted grafts fail the joint bar, by class {dict(sorted(by.items()))}; {len(trig)} admitted grafts carry a trigger"
    return [dict(unit=f"{len(rows)} grafts", upper=None, lower=None, closed=len(bad) >= 1, note=note)]


def reversal_without_attention():
    """RO-1. A first-layer packet reaches reversal with attention frozen and the native skills kept: the sector is open."""
    out = []
    ctl = load(RECHECK / "tf" / "partB_summary.json")["controls"]["ctl_mlp_only_r64_blk1"]
    for seed, acc in sorted(ctl.items(), key=lambda kv: int(kv[0])):
        ok = acc["3"] >= 0.99 and acc["0"] >= 0.98 and acc["1"] >= 0.98
        out.append(dict(unit=f"seed {seed}", upper=None, lower=None, closed=ok,
                        note=f"first-layer packet: reversal {acc['3']:g}, native skills {acc['0']:g} and {acc['1']:g}"))
    retrained = [e["variants"]["mlp@rev"]["final"] for name in ("step5_a.json", "step5_b.json", "step5_lead_seeds_11_12.json")
                 for e in load(RECHECK / "tf" / name)]
    n = sum(f["3"] >= 1.0 for f in retrained)
    out.append(dict(unit="retraining, 10 seeds", upper=None, lower=None, closed=None,
                    note=f"all position-wise layers retrained on reversal alone reach it on {n} of {len(retrained)} seeds and lose the native skills (largest {max(max(f['0'], f['1']) for f in retrained):g})"))
    return out


def quant_hosts():
    """The numbers closure_quant.py saved, checked against the calibration record they were rebuilt from."""
    hosts = load(HERE / "closure_quant.json")["hosts"]
    res = load(CAL / "results.json")
    for h, host, ph in zip(hosts, res["hosts"], res["analysis"]["per_host"]):
        fine = next(x for x in host["rows"] if x["natural"] and x["class"] == "finetune_joint")
        if h["seed"] != ph["seed"] or abs(h["finetune_r"] - fine["r"]) > 1e-9 * fine["r"] or h["break_r"] != ph["H6_r_break_adv"]:
            raise SystemExit("FAIL: closure_quant.json does not match the calibration record; rerun closure_quant.py")
        # The two witnesses are checked here against the record, not taken from the saved file.
        harm = [x for x in host["rows"] if x["class"] == "adv" and not x["natural"] and h["break_r"] is not None and abs(x["r"] - h["break_r"]) <= 1e-12]
        h["break_drop"] = harm[0]["drop"] if harm else None
        h["breaks"] = bool(harm) and harm[0]["drop"] > BAR
        h["finetune_passes"] = fine["drop"] <= BAR and fine["novel_r2_after"] >= NOVEL_MIN
    return hosts


def quotient_ball_gate():
    """CL-5. A breaking move is shorter than a lower bound on the passing fine-tune's distance after any relabelling."""
    out = []
    for h in quant_hosts():
        upper, lower = h["break_r"], h["finetune_quotient_lower"]
        blind = h["relabel_held"] <= SILENT and h["relabel_quotient_lower"] <= SILENT and h["relabel_r"] > 1.0
        ok = h["breaks"] and h["finetune_passes"] and upper < lower <= h["finetune_r"] and blind
        out.append(dict(unit=f"MLP host {h['seed']}", upper=upper, lower=lower, closed=ok,
                        note=f"the fine-tune has length {h['finetune_r']:.2f}; a relabelling of length {h['relabel_r']:.1f} "
                             f"changes outputs by {h['relabel_held']:.1e} and has lower bound {h['relabel_quotient_lower']:.1e}"))
    return out


def ball_gate_rounded_copy():
    """CL-6. A breaking move is shorter than the rounding error of a copy that keeps the bar."""
    out = []
    for h in quant_hosts():
        for b in h["bits"]:
            if b["bits"] in (5, 6, 7):
                keeps = b["drop"] <= BAR
                ok = (h["breaks"] and h["break_r"] < b["length"]) if keeps else None
                out.append(dict(unit=f"MLP host {h['seed']}, {b['bits']} bits", upper=h["break_r"], lower=b["length"], closed=ok,
                                note=f"the rounded copy drops the native score by {b['drop']:.4f}" + ("" if keeps else ", over the bar: no benign witness")))
    return out


def grid_step_in_proved_ball():
    """CL-7. The smallest step of the grid is longer than the radius Theorem 1 proves around the rounded cell."""
    out = []
    for h in quant_hosts():
        for b in h["bits"]:
            if b["bits"] in (5, 6, 7):
                keeps = b["drop"] <= BAR
                ok = (b["safe_radius"] < b["min_step"]) if keeps else None
                out.append(dict(unit=f"MLP host {h['seed']}, {b['bits']} bits", upper=b["safe_radius"], lower=b["min_step"], closed=ok,
                                note=f"the rounded cell drops the native score by {b['drop']:.4f}"))
    return out


def persistence_ball_gate():
    """CL-8. A breaking move is shorter than the largest gap of the passing fine-tune. Hosts where it is not stay open."""
    hosts = load(HERE / "closure_persist.json")["hosts"]
    res = load(CAL / "results.json")
    out = []
    for h, host, ph in zip(hosts, res["hosts"], res["analysis"]["per_host"]):
        fine = next(x for x in host["rows"] if x["natural"] and x["class"] == "finetune_joint")
        if h["seed"] != ph["seed"] or abs(h["finetune_r"] - fine["r"]) > 1e-9 * fine["r"] or h["break_r"] != ph["H6_r_break_adv"]:
            raise SystemExit("FAIL: closure_persist.json does not match the calibration record; rerun closure_persist.py")
        harm = [x for x in host["rows"] if x["class"] == "adv" and not x["natural"] and h["break_r"] is not None and abs(x["r"] - h["break_r"]) <= 1e-12]
        breaks = bool(harm) and harm[0]["drop"] > BAR
        passes = fine["drop"] <= BAR and fine["novel_r2_after"] >= NOVEL_MIN
        upper, lower = h["break_r"], h["finetune_largest_gap"]
        if lower > h["finetune_r"] * (1 + 1e-12):
            raise SystemExit("FAIL: a largest gap exceeds the length of its move")
        crossed = breaks and passes and upper < lower
        out.append(dict(unit=f"MLP host {h['seed']}", upper=upper, lower=lower, closed=True if crossed else None,
                        note=f"the fine-tune has length {h['finetune_r']:.2f}" + ("" if crossed else ". Its largest gap is not above the breaking move, so the host is left open")))
    return out


CHECKS = {f.__name__: f for f in (plasm_linear_cell, ball_gate_nonlinear, probe_threshold_known_probes,
                                  admission_rule_sufficient, reversal_without_attention,
                                  quotient_ball_gate, ball_gate_rounded_copy, grid_step_in_proved_ball,
                                  persistence_ball_gate)}


def fmt(x):
    return "-" if x is None else f"{x:.4g}"


def close_paths(needs, closed):
    """Least set that holds `closed` and every path needing one of its members.

    `needs` maps a path to the sectors or paths it needs. A path needs all of
    them, so one closed member closes it.
    """
    shut = set(closed)
    changed = True
    while changed:
        changed = False
        for path, req in needs.items():
            if path not in shut and shut.intersection(req):
                shut.add(path)
                changed = True
    return shut


def selftest():
    chain = {"a": ["X"], "b": ["a"], "c": ["b", "Y"], "d": ["Y"], "e": ["f"], "f": ["e"]}
    once = close_paths(chain, {"X"})
    if once != {"X", "a", "b", "c"} or close_paths(chain, once) != once or not once <= close_paths(chain, {"X", "Y"}):
        raise SystemExit("FAIL: the path closure is not extensive, monotone and idempotent on the self-test")


def main():
    selftest()
    reg = load(HERE / "closures.json")
    state, failed = {}, False
    for group, word in (("closures", "closed"), ("reopened", "open")):
        for c in reg[group]:
            units = CHECKS[c["check"]]()
            claimed = [u for u in units if u["closed"] is not None]
            held = [u for u in claimed if u["closed"]]
            ok = bool(claimed) and len(held) == len(claimed)
            failed |= not ok
            state[c["id"]] = "closed" if (group == "closures" and ok) else "open"
            what = "certificate" if group == "closures" else "witness"
            print(f"{c['id']} [{c['kind']}] {what + ' holds' if ok else what.upper() + ' FAILS'} on {len(held)} of {len(claimed)} units"
                  + (f" ({len(units) - len(claimed)} not counted)" if len(units) != len(claimed) else "") + f": sector is {state[c['id']]}")
            print(f"   {c['sector']}")
            if c["kind"] == "crossed_bounds":
                gaps = [u["lower"] / u["upper"] for u in held if u["upper"]]
                print(f"   no value of the {c['parameter']} meets both bounds; lower / upper runs from {min(gaps):.3g} to {max(gaps):.3g}")
            for u in units:
                mark = "not counted" if u["closed"] is None else ("holds" if u["closed"] else "FAILS")
                bounds = f"upper {fmt(u['upper'])}  lower {fmt(u['lower'])}  " if c["kind"] == "crossed_bounds" else ""
                print(f"     {u['unit']:<24} {bounds}{mark}; {u['note']}")
            print()
    print("Paths (what each needs is listed by hand in closures.json)")
    needs = {p["id"]: p["needs"] for p in reg["paths"]}
    shut = close_paths(needs, {k for k, v in state.items() if v == "closed"})
    for p in reg["paths"]:
        why = [s for s in p["needs"] if s in shut]
        print(f"   {p['id']} {'CLOSED by ' + ', '.join(why) if p['id'] in shut else 'open':<16} {p['path']}")
    if failed:
        print("\nFAIL: a registered certificate does not hold")
        sys.exit(1)
    print("\nall registered certificates hold")


if __name__ == "__main__":
    main()
