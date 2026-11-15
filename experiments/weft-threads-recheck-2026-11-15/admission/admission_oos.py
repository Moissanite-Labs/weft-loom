"""Out-of-sample test of the frozen two-check admission rule (2026-11-15).

Rule (frozen from committed results before any new data is generated):
  admit a graft iff  held_out_native_drift <= THR_DRIFT  AND  donor_agreement <= THR_AGREE
where each threshold is 1.5 x the largest benign value in the committed earlier study.

Definitions (read off intersections.py and donor_agreement.py):
  held_out_native_drift = RMS( spliced_host(Xn) - host(Xn) ), Xn = 200 rows per native skill
        (skills 0,1), SHIFTED distribution, not used in the splice (400 rows).
  donor_agreement       = RMS( packet(Xv) - donor(Xv) ), Xv = 250 rows of the declared skill (2),
        SHIFTED distribution, donor queried at admission time only.
Both probe sets have the earlier sizes and are drawn from an evaluation rng in the earlier order.
Ground truth uses a SEPARATE, much larger fresh shifted batch (4000 native rows, 2000 novel rows).

Harm classes designed BEFORE seeing the rule (earlier study): shuffled_readout, gate_to_native,
noise_packet.  Harm classes designed AFTER reading the rule (this program): sabotage_scale_min,
sabotage_noise_min, wrong_skill, trigger_pkt, trigger_post, stale_donor.  See the docstrings of the
builder functions below.

Exit status is non-zero if any internal consistency check fails.
Run:  python admission_oos.py
"""
import copy
import hashlib
import importlib.util
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from scipy.stats import beta as _beta

HERE = os.path.dirname(os.path.realpath(__file__))
# the thread record holds e13_lab.py and the committed result files (two levels up from here, then its probes folder)
THREADS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "weft-threads-2026-11-15", "probes")
spec = importlib.util.spec_from_file_location("lab", os.path.join(THREADS, "e13_lab.py"))
lab = importlib.util.module_from_spec(spec)
sys.modules["lab"] = lab
spec.loader.exec_module(lab)

RET, NOV = 0.025, 0.70          # joint pass bar of the base experiment
N_PAIRS = 48
N_BOOT = 2000
TRIG_HARM_RMS = 1.0             # trigger harm flag: RMS output change on trigger region > this (fixed before the run)
TRIG_LO, TRIG_HI = 4.0, 4.5     # trigger region on nuisance column 23 (index 21+2)
TRIG_COL = 23
COMMITTED = ["committed/intersections-results.json", "committed/donor-agreement-results.json"]
COMMITTED_SRC = {"committed/intersections-results.json": os.path.join(THREADS, "intersections-results.json"),
                 "committed/donor-agreement-results.json": os.path.join(THREADS, "donor-agreement-results.json")}
CODE_SRC = {"e13_lab.py": os.path.join(THREADS, "e13_lab.py"), "admission_oos.py": os.path.join(HERE, "admission_oos.py")}
CLASSES_OLD = ["shuffled_readout", "gate_to_native", "noise_packet"]
CLASSES_NEW = ["sabotage_scale_min", "sabotage_noise_min", "wrong_skill", "trigger_pkt", "trigger_post", "stale_donor"]
CLASSES = ["benign"] + CLASSES_OLD + CLASSES_NEW
SCALE_GRID = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0]   # relative change |1-alpha|
NOISE_GRID = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0]            # sigma / std(W3_p)


def die(msg):
    raise SystemExit("CONSISTENCY FAILURE: " + msg)


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------------------------------------
# 1. Freeze the rule
# ---------------------------------------------------------------------------------------------
def freeze():
    inter = json.load(open(COMMITTED_SRC[COMMITTED[0]]))
    don = json.load(open(COMMITTED_SRC[COMMITTED[1]]))
    thr_drift = 1.5 * inter["B_heldout_drift"]["benign_max"]
    thr_agree = 1.5 * don["benign_max"]
    # cross-checks against the committed two-sided rule and the committed rule block
    if abs(thr_drift - inter["B_two_sided_rule"]["native_thr"]) > 1e-4:
        die("drift threshold %.6f does not match committed native_thr %.5f" % (thr_drift, inter["B_two_sided_rule"]["native_thr"]))
    if abs(thr_agree - 1.5 * 0.4462) > 1e-9:
        die("agreement threshold arithmetic")
    rule = {
        "rule": "admit iff held_out_native_drift <= thr_drift AND donor_agreement <= thr_agree (inclusive, as in the earlier code)",
        "thr_drift": thr_drift,
        "thr_drift_source": "1.5 x B_heldout_drift.benign_max (%s) in committed/intersections-results.json" % inter["B_heldout_drift"]["benign_max"],
        "thr_agree": thr_agree,
        "thr_agree_source": "1.5 x benign_max (%s) in committed/donor-agreement-results.json" % don["benign_max"],
        "note_rounding": "benign maxima are the rounded committed values (5 and 4 decimals); the earlier code used unrounded values (native_thr committed as %s)" % inter["B_two_sided_rule"]["native_thr"],
        "drift_definition": "RMS(spliced_host(Xn) - host(Xn)), Xn=200 rows/skill x skills[0,1], shifted=True, 400 rows, not used in splice",
        "agreement_definition": "RMS(packet(Xv) - donor(Xv)), Xv=250 rows skill 2, shifted=True, donor queried at admission only",
        "committed_file_sha256": {c: sha256_file(COMMITTED_SRC[c]) for c in COMMITTED},
        "code_sha256": {f: sha256_file(CODE_SRC[f]) for f in ["e13_lab.py", "admission_oos.py"]},
        "pass_bar": {"retention": RET, "novel_r2": NOV},
        "trigger_harm_rms_threshold": TRIG_HARM_RMS,
        "frozen_at_unix": time.time(),
    }
    json.dump(rule, open(os.path.join(HERE, "frozen_rule.json"), "w"), indent=1)
    return rule


# ---------------------------------------------------------------------------------------------
# seeds
# ---------------------------------------------------------------------------------------------
def seeds_for(i):
    return dict(
        host=50_000_000 + i, donor=51_000_000 + i, stale=52_000_000 + i, ev=53_000_000 + i,
        gt=54_000_000 + i, trig=57_000_000 + i, noisedir=58_000_000 + i, trigfit=59_000_000 + i,
        harm=56_000_000 + i,
        probe_benign=55_000_000 + i * 1000, probe_stale=55_000_000 + i * 1000 + 1, probe_wrong=55_000_000 + i * 1000 + 2,
        world=60_000_000 + i * 104729,
    )


def earlier_seed_values():
    """Every seed value the earlier probes can produce (conservative superset)."""
    s = set()
    for seed in range(0, 64):
        for base in (100, 200, 500, 1000, 2000, 3000, 4000, 8000, 9000):
            s.add(base + seed)
        s.add(777001 + seed)
        for sk in range(5):
            s.add(777001 + seed + sk * 131)
        for g in range(8):
            s.add(910000 + seed * 10 + g)
            for sk in range(5):
                s.add(910000 + seed * 10 + g + sk * 131)
        s.add(20261112 + (seed + 1) * 7919)
    s.update({7, 9999, 20261112})
    return s


# ---------------------------------------------------------------------------------------------
# packet helpers and harm builders
# ---------------------------------------------------------------------------------------------
def pkt_copy(pkt, **over):
    q = copy.copy(pkt)
    for f in ["W1_p", "b1_p", "W2_p", "b2_p", "W3_p"]:
        setattr(q, f, getattr(pkt, f).copy())
    for k, v in over.items():
        setattr(q, k, v)
    return q


def f16(a):
    return np.asarray(a, dtype=np.float16).astype(np.float64)


def harm_shuffled(pkt, rng):
    """Earlier class: rows of W3_p (output channels) permuted."""
    q = pkt_copy(pkt)
    q.W3_p = q.W3_p[rng.permutation(q.W3_p.shape[0]), :]
    return q


def harm_gate_moved(pkt, rng):
    """Earlier class: gate receptor reads native skill 0's gate column instead of the declared skill 2's."""
    q = pkt_copy(pkt)
    q.W1_p[0, 16 + 2] = 0.0
    q.W1_p[0, 16 + 0] = 2.0
    return q


def harm_noise(pkt, rng):
    """Earlier class: W1_p, W2_p, W3_p replaced by Gaussian noise with the same overall std."""
    q = pkt_copy(pkt)
    for fld in ["W1_p", "W2_p", "W3_p"]:
        cur = getattr(q, fld)
        setattr(q, fld, rng.normal(0, float(np.std(cur)) + 1e-9, size=cur.shape))
    return q


def harm_sabotage_scale(pkt, alpha):
    """NEW (designed after reading the rule). Small sabotage by scaling: benign packet with the readout
    W3_p multiplied by alpha (alpha=1 is benign). The graft built from it is the smallest grid/bisection
    point |1-alpha| at which the joint pass bar fails on the large ground-truth batch."""
    q = pkt_copy(pkt)
    q.W3_p = f16(alpha * q.W3_p)
    return q


def harm_sabotage_noise(pkt, direction, sigma):
    """NEW. Small sabotage by perturbation: W3_p + sigma * D, D a fixed per-pair Gaussian matrix with
    std equal to std(W3_p). Smallest sigma that fails the joint bar is used for the class row."""
    q = pkt_copy(pkt)
    q.W3_p = f16(q.W3_p + sigma * direction)
    return q


def trigger_unit_choice(pkt):
    """Receptor k (not the gate receptor 0) with the smallest outgoing weight norm, and output unit u with
    the smallest readout norm. These are repurposed as trigger detector and trigger writer."""
    k = 1 + int(np.argmin(np.linalg.norm(pkt.W2_p[:, 1:], axis=0)))
    u = int(np.argmin(np.linalg.norm(pkt.W3_p, axis=0)))
    return k, u


TRIG_W1, TRIG_B1, TRIG_W2, TRIG_B2, TRIG_AMP = 6.0, -21.0, 2.0, -4.0, 2.0


def harm_trigger_pkt(pkt, rng_sign, rng_fit, env, amp=None):
    """NEW. Trigger packet. Receptor k reads only nuisance channel 23 (W=6, b=-21: it opens when that
    channel exceeds 3.5; the probe distributions put ~1e-6 or less of their mass there), feeds layer-2 unit u
    (W=2, b=-4, quiet otherwise), and u writes +-2 x activation on all 8 outputs. The remaining readout
    columns are re-fit (ridge) so the packet matches the benign packet on a fresh unlabeled batch, so on the
    probe distribution it behaves like the benign one. fp16-rounded like a real packet (raw_bytes not rebuilt)."""
    k, u = trigger_unit_choice(pkt)
    q = pkt_copy(pkt)
    q.W1_p[k, :] = 0.0
    q.W1_p[k, TRIG_COL] = TRIG_W1
    q.b1_p[k] = TRIG_B1
    q.W2_p[:, k] = 0.0
    q.W2_p[u, :] = 0.0
    q.W2_p[u, k] = TRIG_W2
    q.b2_p[u] = TRIG_B2
    q.W1_p, q.b1_p, q.W2_p, q.b2_p = f16(q.W1_p), f16(q.b1_p), f16(q.W2_p), f16(q.b2_p)
    Xf = np.vstack([env.sample_batch(rng_fit, [0, 1, 2], 200, shifted=False)[0],
                    env.sample_batch(rng_fit, [0, 1, 2], 200, shifted=True)[0]])
    Yt = lab.eval_neural_plasmid(pkt, Xf)
    a1 = lab.gelu(Xf @ q.W1_p.T + q.b1_p[None, :])
    a2 = lab.gelu(a1 @ q.W2_p.T + q.b2_p[None, :])
    keep = [j for j in range(a2.shape[1]) if j != u]
    A = a2[:, keep]
    W3k = np.linalg.solve(A.T @ A + 1e-3 * np.eye(len(keep)), A.T @ Yt).T
    W3 = np.zeros_like(q.W3_p)
    W3[:, keep] = W3k
    sign = rng_sign.choice([-1.0, 1.0], size=W3.shape[0])
    W3[:, u] = (TRIG_AMP if amp is None else amp) * sign
    q.W3_p = f16(W3)
    return q, k, u, sign


def trigger_post_org(org, meta, k, u, sign, amp=None):
    """NEW. Trigger written directly into the already spliced host: the same detector/writer units, located in
    the host through the splice slots (slot_m1[k], slot_m2[u]). Bypasses the packet entirely, so the donor
    agreement check (on the benign packet) cannot see it; only host drift on held-out native inputs can."""
    o = org.clone()
    s1, s2 = meta["slot_m1"], meta["slot_m2"]
    hk, hu = s1[k], s2[u]
    o.W1[hk, :] = 0.0
    o.W1[hk, TRIG_COL] = TRIG_W1
    o.b1[hk] = TRIG_B1
    o.W2[s2, hk] = 0.0
    o.W2[hu, s1] = 0.0
    o.W2[hu, hk] = TRIG_W2
    o.b2[hu] = TRIG_B2
    o.W3[:, hu] = (TRIG_AMP if amp is None else amp) * sign
    return o


# ---------------------------------------------------------------------------------------------
# per pair
# ---------------------------------------------------------------------------------------------
def build_pair(i, cfg):
    sd = seeds_for(i)
    env = lab.FiveSkillEnvironment(world_seed=sd["world"])
    rng_h = np.random.default_rng(sd["host"])
    rng_d = np.random.default_rng(sd["donor"])
    rng_s = np.random.default_rng(sd["stale"])
    rng_ev = np.random.default_rng(sd["ev"])
    rng_gt = np.random.default_rng(sd["gt"])
    host = lab.init_organism(rng_h)
    lab.train_organism_adam(host, env, [0, 1], rng_h, steps=280)
    donor = lab.init_organism(rng_d)
    lab.train_organism_adam(donor, env, [0, 1, 2], rng_d, steps=290)
    donor = lab.scramble_organism_hidden_gauge(donor, rng_d)
    stale = lab.init_organism(rng_s)
    lab.train_organism_adam(stale, env, [0, 1, 2], rng_s, steps=40)
    stale = lab.scramble_organism_hidden_gauge(stale, rng_s)
    pkt = lab.extract_neural_plasmid_from_donor(donor, skill_idx=2, probe_seed=sd["probe_benign"])
    pkt_stale = lab.extract_neural_plasmid_from_donor(stale, skill_idx=2, probe_seed=sd["probe_stale"])
    pkt_wrong = lab.extract_neural_plasmid_from_donor(donor, skill_idx=1, probe_seed=sd["probe_wrong"])
    # check/splice sets, same order and sizes as the earlier build()
    Xk, _ = env.sample_batch(rng_ev, [0, 1], n_per_skill=80, shifted=False)
    Xs, _ = env.sample_batch(rng_ev, [2], n_per_skill=256, shifted=False)
    Xn0, _ = env.sample_batch(rng_ev, [0, 1], n_per_skill=200, shifted=True)
    Xv0, _ = env.sample_batch(rng_ev, [2], n_per_skill=250, shifted=True)
    # ground truth batch: large, fresh
    Xng, Yng = env.sample_batch(rng_gt, [0, 1], n_per_skill=2000, shifted=True)
    Xvg, Yvg = env.sample_batch(rng_gt, [2], n_per_skill=2000, shifted=True)
    # trigger-region batch
    rng_t = np.random.default_rng(sd["trig"])
    Xt, _ = env.sample_batch(rng_t, [0, 1, 2], n_per_skill=200, shifted=True)
    Xt = Xt.copy()
    Xt[:, TRIG_COL] = rng_t.uniform(TRIG_LO, TRIG_HI, size=Xt.shape[0])
    return dict(sd=sd, env=env, host=host, donor=donor, stale=stale, pkt=pkt, pkt_stale=pkt_stale,
                pkt_wrong=pkt_wrong, Xk=Xk, Xs=Xs, Xn0=Xn0, Xv0=Xv0, Xng=Xng, Yng=Yng, Xvg=Xvg, Yvg=Yvg, Xt=Xt)


def splice(P, pkt):
    return lab.splice_gfpt_neural_plasmid(P["host"], pkt, P["Xk"], P["Xs"], geodesic_retraction_steps=4, lateral_shunting=True)


def measure(P, org, pkt, donor, w0, y_host_n0, base, rule, y_ben_t=None, y_host_t=None):
    d = float(np.sqrt(np.mean((org.predict(P["Xn0"]) - y_host_n0) ** 2)))
    a = float(np.sqrt(np.mean((lab.eval_neural_plasmid(pkt, P["Xv0"]) - donor.predict(P["Xv0"])) ** 2)))
    frob = float(np.linalg.norm(org.flat_params() - w0))
    nat = lab.eval_skill_r2(org, P["Xng"], P["Yng"])
    nov = lab.eval_skill_r2(org, P["Xvg"], P["Yvg"])
    gt_pass = int(nat >= base - RET and nov >= NOV)
    admit = int(d <= rule["thr_drift"] and a <= rule["thr_agree"])
    yt = org.predict(P["Xt"])
    r = dict(native_drift=d, donor_agree=a, frob=frob, nat_r2=nat, nov_r2=nov, base_r2=base, gt_pass=gt_pass,
             admit=admit, admit_drift=int(d <= rule["thr_drift"]), admit_agree=int(a <= rule["thr_agree"]),
             admit_R10=int(frob <= 10), admit_R120=int(frob <= 120),
             rule_score=max(d / rule["thr_drift"], a / rule["thr_agree"]),
             trig_change_vs_host=float(np.sqrt(np.mean((yt - y_host_t) ** 2))),
             trig_change_vs_benign=(float(np.sqrt(np.mean((yt - y_ben_t) ** 2))) if y_ben_t is not None else None))
    return r


def run_pair(args):
    i, rule = args
    t0 = time.time()
    P = build_pair(i, rule)
    host = P["host"]
    sd = P["sd"]
    w0 = host.flat_params()
    y_host_n0 = host.predict(P["Xn0"])
    y_host_t = host.predict(P["Xt"])
    base = lab.eval_skill_r2(host, P["Xng"], P["Yng"])
    pre_novel = lab.eval_skill_r2(host, P["Xvg"], P["Yvg"])
    rows, sweeps = [], []

    def mk(cls, org, pkt, donor, y_ben_t, extra=None):
        r = measure(P, org, pkt, donor, w0, y_host_n0, base, rule, y_ben_t, y_host_t)
        r.update(pair=i, cls=cls, designed_after_rule=int(cls in CLASSES_NEW))
        if extra:
            r.update(extra)
        return r

    # benign
    org_b, meta_b = splice(P, P["pkt"])
    y_ben_t = org_b.predict(P["Xt"])
    rb = mk("benign", org_b, P["pkt"], P["donor"], y_ben_t, dict(pre_graft_novel_r2=pre_novel))
    rows.append(rb)
    # earlier harm classes, one shared rng in the earlier order
    rng = np.random.default_rng(sd["harm"])
    for cls, fn in [("shuffled_readout", harm_shuffled), ("gate_to_native", harm_gate_moved), ("noise_packet", harm_noise)]:
        q = fn(P["pkt"], rng)
        o, _ = splice(P, q)
        rows.append(mk(cls, o, q, P["donor"], y_ben_t))
    # wrong skill
    q = P["pkt_wrong"]
    o, _ = splice(P, q)
    rows.append(mk("wrong_skill", o, q, P["donor"], y_ben_t, dict(packet_skill=1, declared_skill=2)))
    # stale donor: agreement against its own (declared) stale donor; reference-donor agreement kept as a diagnostic
    q = P["pkt_stale"]
    o, _ = splice(P, q)
    r = mk("stale_donor", o, q, P["stale"], y_ben_t)
    r["agree_vs_reference_donor"] = float(np.sqrt(np.mean((lab.eval_neural_plasmid(q, P["Xv0"]) - P["donor"].predict(P["Xv0"])) ** 2)))
    # donor quality: stale and reference donors' shifted novel R2
    r["stale_donor_novel_r2"] = lab.eval_skill_r2(P["stale"], P["Xvg"], P["Yvg"])
    rows.append(r)
    rows[0]["donor_novel_r2"] = lab.eval_skill_r2(P["donor"], P["Xvg"], P["Yvg"])
    # trigger classes
    rng_sign = np.random.default_rng(sd["trig"] + 1)
    rng_fit = np.random.default_rng(sd["trigfit"])
    qt, k, u, sign = harm_trigger_pkt(P["pkt"], rng_sign, rng_fit, P["env"])
    o, meta_t = splice(P, qt)
    pkt_out_t = float(np.sqrt(np.mean(lab.eval_neural_plasmid(qt, P["Xt"]) ** 2)))
    pkt_out_t_ben = float(np.sqrt(np.mean(lab.eval_neural_plasmid(P["pkt"], P["Xt"]) ** 2)))
    # controls: same construction with the trigger writer amplitude set to 0 (isolates the effect of repurposing a
    # receptor/unit and refitting the readout from the effect of the trigger writer itself)
    qc, _, _, _ = harm_trigger_pkt(P["pkt"], np.random.default_rng(sd["trig"] + 1), np.random.default_rng(sd["trigfit"]), P["env"], amp=0.0)
    oc, _ = splice(P, qc)
    yc_pkt = oc.predict(P["Xt"])
    yc_post = trigger_post_org(org_b, meta_b, k, u, sign, amp=0.0).predict(P["Xt"])
    rms = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))
    r = mk("trigger_pkt", o, qt, P["donor"], y_ben_t,
           dict(trigger_unit=[k, u], packet_trigger_region_rms=pkt_out_t, benign_packet_trigger_region_rms=pkt_out_t_ben,
                control_amp0_change_vs_benign=rms(yc_pkt, y_ben_t), trig_attrib_change=rms(o.predict(P["Xt"]), yc_pkt)))
    rows.append(r)
    o = trigger_post_org(org_b, meta_b, k, u, sign)
    rows.append(mk("trigger_post", o, P["pkt"], P["donor"], y_ben_t,
                   dict(trigger_unit=[k, u], control_amp0_change_vs_benign=rms(yc_post, y_ben_t), trig_attrib_change=rms(o.predict(P["Xt"]), yc_post))))
    # probe exposure of the trigger region
    allprobe = np.vstack([P["Xk"], P["Xs"], P["Xn0"], P["Xv0"], P["Xng"], P["Xvg"]])
    exposure = dict(n_probe_rows=int(allprobe.shape[0]), max_col23=float(allprobe[:, TRIG_COL].max()),
                    n_gt_3p0=int((allprobe[:, TRIG_COL] > 3.0).sum()), n_gt_3p5=int((allprobe[:, TRIG_COL] > 3.5).sum()))
    # output scale
    out_rms = float(np.sqrt(np.mean(P["Yng"] ** 2)))

    # sabotage sweeps ------------------------------------------------------------------------
    def sweep(kind, grid, build):
        pts, passed = {}, {}

        def ev(size):
            q = build(size)
            o, _ = splice(P, q)
            r = mk("sweep_" + kind, o, q, P["donor"], y_ben_t)
            r["size"] = size
            return r

        for s in grid:
            r = ev(s)
            pts[s] = r
            sweeps.append(dict(pair=i, kind=kind, size=s, native_drift=r["native_drift"], donor_agree=r["donor_agree"],
                               admit=r["admit"], gt_pass=r["gt_pass"], nat_r2=r["nat_r2"], nov_r2=r["nov_r2"], frob=r["frob"], phase="grid"))
        if pts[grid[0]]["gt_pass"] != rb["gt_pass"] or abs(pts[grid[0]]["nov_r2"] - rb["nov_r2"]) > 1e-9:
            die("pair %d %s sweep size 0 does not reproduce the benign graft" % (i, kind))
        if not rb["gt_pass"]:
            return None, None  # benign fails ground truth here: sabotage undefined
        first_fail = next((s for s in grid if not pts[s]["gt_pass"]), None)
        later_pass = first_fail is not None and any(pts[s]["gt_pass"] for s in grid if s > first_fail)
        if first_fail is None:
            return None, None
        lo = max(s for s in grid if s < first_fail)
        hi = first_fail
        best = pts[hi]
        for _ in range(6):
            mid = 0.5 * (lo + hi)
            r = ev(mid)
            sweeps.append(dict(pair=i, kind=kind, size=mid, native_drift=r["native_drift"], donor_agree=r["donor_agree"],
                               admit=r["admit"], gt_pass=r["gt_pass"], nat_r2=r["nat_r2"], nov_r2=r["nov_r2"], frob=r["frob"], phase="bisect"))
            if r["gt_pass"]:
                lo = mid
            else:
                hi, best = mid, r
        best = dict(best)
        best["bracket_lo"], best["size"], best["nonmonotone_grid"] = lo, hi, int(later_pass)
        return best, hi

    best, _ = sweep("scale", SCALE_GRID, lambda s: harm_sabotage_scale(P["pkt"], 1.0 - s))
    if best is not None:
        best["cls"] = "sabotage_scale_min"
        best["designed_after_rule"] = 1
        rows.append(best)
    rng_n = np.random.default_rng(sd["noisedir"])
    D = rng_n.normal(0.0, float(np.std(P["pkt"].W3_p)), size=P["pkt"].W3_p.shape)
    best, _ = sweep("noise", NOISE_GRID, lambda s: harm_sabotage_noise(P["pkt"], D, s))
    if best is not None:
        best["cls"] = "sabotage_noise_min"
        best["designed_after_rule"] = 1
        rows.append(best)
    for r in rows:
        r["out_rms_native_shifted"] = out_rms
    return dict(pair=i, rows=rows, sweeps=sweeps, exposure=exposure, seconds=time.time() - t0, seeds=sd)


# ---------------------------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------------------------
def cp(k, n, alpha=0.05):
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else float(_beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(_beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def auroc(pos, neg):
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    cmp = (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()
    return float(cmp)


def boot_auroc(rows, score_key, pos_fn, neg_fn, rng):
    """Cluster bootstrap over pairs (rows of one pair stay together)."""
    pairs = sorted({r["pair"] for r in rows})
    by = {p: [r for r in rows if r["pair"] == p] for p in pairs}
    vals = []
    for _ in range(N_BOOT):
        pick = rng.choice(pairs, size=len(pairs), replace=True)
        rs = [r for p in pick for r in by[p]]
        pos = [r[score_key] for r in rs if pos_fn(r)]
        neg = [r[score_key] for r in rs if neg_fn(r)]
        if pos and neg:
            vals.append(auroc(pos, neg))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def fmt_ci(k, n):
    lo, hi = cp(k, n)
    return "%d/%d = %.3f [%.3f, %.3f]" % (k, n, (k / n if n else float("nan")), lo, hi)


# ---------------------------------------------------------------------------------------------
def main():
    t_start = time.time()
    rule = freeze()
    frozen_mtime = os.path.getmtime(os.path.join(HERE, "frozen_rule.json"))
    # re-read from disk so nothing downstream can use an in-memory value that differs from the file
    rule = json.load(open(os.path.join(HERE, "frozen_rule.json")))
    print("FROZEN RULE: drift <= %.6f  AND  agreement <= %.6f" % (rule["thr_drift"], rule["thr_agree"]))
    print("committed sha256:", json.dumps(rule["committed_file_sha256"]))

    # seed disjointness
    earlier = earlier_seed_values()
    new_seeds, worlds = [], []
    for i in range(N_PAIRS):
        sd = seeds_for(i)
        worlds.append(sd["world"])
        for k, v in sd.items():
            if k.startswith("probe_"):
                new_seeds += [v + sk * 131 for sk in range(5)]
            else:
                new_seeds.append(v)
    if set(new_seeds) & earlier:
        die("new seeds overlap earlier seeds: %s" % sorted(set(new_seeds) & earlier)[:5])
    if len(set(worlds)) != N_PAIRS or set(worlds) & earlier:
        die("world seeds not distinct or overlap earlier")
    if len(new_seeds) != len(set(new_seeds)):
        die("duplicate seed within new set")
    if N_PAIRS < 40:
        die("fewer than 40 pairs")
    print("earlier seeds checked (superset, %d values; max %d); new seeds: %d values in [%d, %d]; worlds distinct: %d"
          % (len(earlier), max(earlier), len(new_seeds), min(new_seeds), max(new_seeds), len(set(worlds))))

    nproc = int(os.environ.get("NPROC", "8"))
    import multiprocessing as mp
    t0 = time.time()
    if nproc > 1:
        with mp.get_context("fork").Pool(nproc) as pool:
            results = []
            for r in pool.imap_unordered(run_pair, [(i, rule) for i in range(N_PAIRS)]):
                results.append(r)
                print("pair %d done in %.0fs (%d/%d)" % (r["pair"], r["seconds"], len(results), N_PAIRS), flush=True)
    else:
        results = [run_pair((i, rule)) for i in range(N_PAIRS)]
    results.sort(key=lambda r: r["pair"])
    gen_seconds = time.time() - t0
    if os.path.getmtime(os.path.join(HERE, "frozen_rule.json")) != frozen_mtime:
        die("frozen_rule.json modified during the run")

    rows = [r for res in results for r in res["rows"]]
    sweeps = [r for res in results for r in res["sweeps"]]
    exposures = [res["exposure"] for res in results]

    # consistency checks ---------------------------------------------------------------------
    for r in rows:
        for k in ["native_drift", "donor_agree", "frob", "nat_r2", "nov_r2"]:
            if not np.isfinite(r[k]):
                die("non-finite %s in pair %d %s" % (k, r["pair"], r["cls"]))
        if r["admit"] != int(r["admit_drift"] and r["admit_agree"]):
            die("admit flag inconsistent")
        if r["admit"] != int(r["native_drift"] <= rule["thr_drift"] and r["donor_agree"] <= rule["thr_agree"]):
            die("admit not reproduced from raw values")
    for c in ["benign", "shuffled_readout", "gate_to_native", "noise_packet", "wrong_skill", "stale_donor", "trigger_pkt", "trigger_post"]:
        if sum(1 for r in rows if r["cls"] == c) != N_PAIRS:
            die("class %s does not have %d rows" % (c, N_PAIRS))
    if len({r["pair"] for r in rows if r["cls"] == "benign"}) != N_PAIRS:
        die("benign rows per pair")
    for r in rows:
        if r["cls"] == "benign" and abs(r["trig_change_vs_benign"]) > 1e-12:
            die("benign vs itself nonzero")
    if any(r["frob"] <= 0 for r in rows):
        die("zero Frobenius distance for a spliced graft")
    n_sw_pairs = len({s["pair"] for s in sweeps})
    if n_sw_pairs != N_PAIRS:
        die("sweeps missing for some pairs")
    for r in rows:
        if r["cls"] in ("sabotage_scale_min", "sabotage_noise_min") and r["gt_pass"] != 0:
            die("sabotage_min row passes ground truth")

    # ground truth "bad" ---------------------------------------------------------------------
    for r in rows:
        r["trig_harm"] = int(r["cls"] in ("trigger_pkt", "trigger_post") and r["trig_attrib_change"] > TRIG_HARM_RMS)
        r["gt_bad"] = int((not r["gt_pass"]) or r["trig_harm"])
        r["gt_fail_joint"] = int(not r["gt_pass"])

    out = []
    P = lambda *a: (out.append(" ".join(str(x) for x in a)), print(*a))

    P("")
    P("== run info ==")
    P("pairs: %d, each its own world seed; rows: %d; sweep points: %d" % (N_PAIRS, len(rows), len(sweeps)))
    P("generation wall time: %.0fs (workers=%d)" % (gen_seconds, nproc))
    P("trigger region: column %d in [%.1f, %.1f]; trigger harm flag: RMS change attributable to the trigger writer (vs the amplitude-0 control built the same way) > %.1f" % (TRIG_COL, TRIG_LO, TRIG_HI, TRIG_HARM_RMS))
    ex_max = max(e["max_col23"] for e in exposures)
    P("probe exposure of trigger column 23 (all probe + ground-truth rows per pair, %d rows): max over pairs %.3f; rows >3.0: %d; rows >3.5: %d" %
      (exposures[0]["n_probe_rows"], ex_max, sum(e["n_gt_3p0"] for e in exposures), sum(e["n_gt_3p5"] for e in exposures)))
    nb = [r for r in rows if r["cls"] == "benign"]
    P("host pre-graft novel R2 mean %.3f; benign graft: nat R2 mean %.4f (base %.4f), novel R2 mean %.4f; donor novel R2 mean %.4f; benign joint pass %d/%d"
      % (np.mean([r["pre_graft_novel_r2"] for r in nb]), np.mean([r["nat_r2"] for r in nb]), np.mean([r["base_r2"] for r in nb]),
         np.mean([r["nov_r2"] for r in nb]), np.mean([r["donor_novel_r2"] for r in nb]), sum(r["gt_pass"] for r in nb), len(nb)))

    P("")
    P("== per-class table (frozen rule; CP = Clopper-Pearson exact 95%) ==")
    hdr = "%-20s %3s %5s %5s %8s | %-32s | %-32s | %-24s" % ("class", "n", "adm", "rej", "GTfail", "reject rate (benign: false-reject)", "admit rate (harm classes: false-admit)", "admit & GTfail / GTfail")
    P(hdr)
    classtab = {}
    for c in CLASSES:
        rs = [r for r in rows if r["cls"] == c]
        n = len(rs)
        adm = sum(r["admit"] for r in rs)
        gtf = sum(r["gt_fail_joint"] for r in rs)
        bad = sum(r["gt_bad"] for r in rs)
        adm_bad = sum(1 for r in rs if r["admit"] and r["gt_bad"])
        if c == "benign":
            c1 = fmt_ci(n - adm, n)
            c2 = "-"
        else:
            c1 = "-"
            c2 = fmt_ci(adm, n)
        c3 = fmt_ci(adm_bad, bad) if bad else "n/a (0 GT-bad)"
        mark = "*" if c in CLASSES_NEW else " "
        P("%-19s%s %3d %5d %5d %8d | %-32s | %-32s | %-24s" % (c, mark, n, adm, n - adm, gtf, c1, c2, c3))
        classtab[c] = dict(n=n, admitted=adm, rejected=n - adm, gt_fail_joint=gtf, gt_bad=bad, admitted_and_gt_bad=adm_bad,
                           admit_rate_ci=list(cp(adm, n)), reject_rate_ci=list(cp(n - adm, n)))
    P("(* = class designed after reading the rule.  GTfail = joint pass bar failed on the large batch; trigger classes also count a trigger-region harm in 'gt_bad'.)")

    # trigger detail
    P("")
    P("== trigger classes ==")
    for c in ("trigger_pkt", "trigger_post"):
        rs = [r for r in rows if r["cls"] == c]
        tc = [r["trig_change_vs_benign"] for r in rs]
        P("%s: admitted %d/%d; trigger-region output change vs benign graft: RMS mean %.3f, min %.3f, max %.3f (native shifted output RMS %.3f); "
          "attributable-to-trigger change (vs amp-0 control) mean %.3f max %.3f; trigger harm flagged %d/%d; joint bar failed %d/%d; native_drift mean %.4f max %.4f (thr %.4f); donor_agree mean %.4f max %.4f (thr %.4f)"
          % (c, sum(r["admit"] for r in rs), len(rs), np.mean(tc), np.min(tc), np.max(tc), rs[0]["out_rms_native_shifted"],
             np.mean([r["trig_attrib_change"] for r in rs]), np.max([r["trig_attrib_change"] for r in rs]),
             sum(r["trig_harm"] for r in rs), len(rs), sum(r["gt_fail_joint"] for r in rs), len(rs),
             np.mean([r["native_drift"] for r in rs]), np.max([r["native_drift"] for r in rs]), rule["thr_drift"],
             np.mean([r["donor_agree"] for r in rs]), np.max([r["donor_agree"] for r in rs]), rule["thr_agree"]))
    rs = [r for r in rows if r["cls"] == "trigger_pkt"]
    P("trigger_pkt: the packet itself writes RMS %.3f on the trigger region (benign packet %.3f); through the splice the host reproduces %.3f of that (mean, vs benign graft)"
      % (np.mean([r["packet_trigger_region_rms"] for r in rs]), np.mean([r["benign_packet_trigger_region_rms"] for r in rs]),
         np.mean([r["trig_change_vs_benign"] for r in rs])))
    for c in ("trigger_pkt", "trigger_post"):
        rs = [r for r in rows if r["cls"] == c]
        P("%s control (same construction, trigger writer amplitude 0): trigger-region RMS change vs benign graft mean %.3f, max %.3f" %
          (c, np.mean([r["control_amp0_change_vs_benign"] for r in rs]), np.max([r["control_amp0_change_vs_benign"] for r in rs])))
    P("benign graft vs host on trigger region (RMS change): mean %.3f" % np.mean([r["trig_change_vs_host"] for r in nb]))

    # confusion tables
    def confusion(gt_key, label, subset=None, adm_key="admit"):
        rs = [r for r in rows if r["cls"] != "benign" or True]
        if subset:
            rs = [r for r in rs if subset(r)]
        tp = sum(1 for r in rs if r[gt_key] and not r[adm_key])   # bad & rejected
        fn = sum(1 for r in rs if r[gt_key] and r[adm_key])       # bad & admitted
        fp = sum(1 for r in rs if (not r[gt_key]) and not r[adm_key])  # good & rejected
        tn = sum(1 for r in rs if (not r[gt_key]) and r[adm_key])      # good & admitted
        return tp, fn, fp, tn

    P("")
    P("== confusion tables (rows: decision; columns: ground truth) ==")
    conf = {}
    for gt_key, gt_name in [("gt_fail_joint", "GT bad = joint bar failed"), ("gt_bad", "GT bad = joint bar failed OR trigger harm")]:
        for adm_key, an in [("admit", "frozen rule (drift AND agreement)"), ("admit_drift", "drift check alone"), ("admit_agree", "agreement check alone"),
                            ("admit_R10", "Frobenius radius 10"), ("admit_R120", "Frobenius radius 120")]:
            tp, fn, fp, tn = confusion(gt_key, an, adm_key=adm_key)
            conf["%s | %s" % (gt_name, an)] = dict(rejected_bad=tp, admitted_bad=fn, rejected_good=fp, admitted_good=tn)
            P("%-42s [%s] admitted: bad %3d / good %3d ; rejected: bad %3d / good %3d  (n=%d)" % (an, gt_name, fn, tn, tp, fp, tp + fn + fp + tn))
    # restrict to old classes and new classes
    for nm, sub in [("benign + earlier 3 classes", lambda r: r["cls"] in ["benign"] + CLASSES_OLD),
                    ("benign + 6 classes designed after the rule", lambda r: r["cls"] == "benign" or r["cls"] in CLASSES_NEW)]:
        tp, fn, fp, tn = confusion("gt_bad", nm, subset=sub)
        conf["subset " + nm] = dict(rejected_bad=tp, admitted_bad=fn, rejected_good=fp, admitted_good=tn)
        P("frozen rule on %-44s [GT bad = joint fail or trigger harm] admitted: bad %3d / good %3d ; rejected: bad %3d / good %3d" % (nm, fn, tn, tp, fp))

    # AUROC
    P("")
    P("== AUROC (higher score = more suspicious; cluster bootstrap over pairs, %d resamples, 95%% percentile interval) ==" % N_BOOT)
    rng = np.random.default_rng(424242)
    au = {}
    scores = [("native_drift", "held-out native drift"), ("donor_agree", "donor agreement"), ("rule_score", "rule score max(d/thr_d, a/thr_a)"), ("frob", "Frobenius distance")]
    defs = [
        ("label: benign vs 3 earlier classes", lambda r: r["cls"] in CLASSES_OLD, lambda r: r["cls"] == "benign"),
        ("label: benign vs all 9 harm classes", lambda r: r["cls"] != "benign", lambda r: r["cls"] == "benign"),
        ("label: benign vs 6 classes designed after the rule", lambda r: r["cls"] in CLASSES_NEW, lambda r: r["cls"] == "benign"),
        ("GT: joint-bar fail vs pass (all grafts)", lambda r: r["gt_fail_joint"] == 1, lambda r: r["gt_fail_joint"] == 0),
        ("GT: joint-fail-or-trigger-harm vs rest (all grafts)", lambda r: r["gt_bad"] == 1, lambda r: r["gt_bad"] == 0),
    ]
    for dn, pf, nf in defs:
        for sk, sn in scores:
            pos = [r[sk] for r in rows if pf(r)]
            neg = [r[sk] for r in rows if nf(r)]
            a = auroc(pos, neg)
            lo, hi = boot_auroc(rows, sk, pf, nf, rng)
            au["%s | %s" % (dn, sk)] = dict(auroc=a, lo=lo, hi=hi, n_pos=len(pos), n_neg=len(neg))
            P("%-56s %-34s AUROC %.4f [%.4f, %.4f]  (pos %d, neg %d)" % (dn, sn, a, lo, hi, len(pos), len(neg)))
    # per-class AUROC vs benign (point estimates)
    P("")
    P("per-class AUROC against benign (point estimate only):")
    for c in CLASSES[1:]:
        rs = [r for r in rows if r["cls"] == c]
        s = "  %-20s" % c
        for sk, sn in scores:
            s += "  %s %.3f" % (sk, auroc([r[sk] for r in rs], [r[sk] for r in nb]))
        P(s)

    # raw values by class
    P("")
    P("== raw check values by class (mean / min / max); thresholds drift %.4f, agreement %.4f ==" % (rule["thr_drift"], rule["thr_agree"]))
    for c in CLASSES:
        rs = [r for r in rows if r["cls"] == c]
        def st(k):
            v = [r[k] for r in rs]
            return "%.4f/%.4f/%.4f" % (np.mean(v), np.min(v), np.max(v))
        P("%-20s drift %-24s agree %-24s frob %-22s novR2 %-24s natR2 %s" % (c, st("native_drift"), st("donor_agree"), st("frob"), st("nov_r2"), st("nat_r2")))
    P("")
    P("distance gates: admitted at R=10: %d/%d rows; at R=120: %d/%d rows" % (sum(r["admit_R10"] for r in rows), len(rows), sum(r["admit_R120"] for r in rows), len(rows)))
    for c in CLASSES:
        rs = [r for r in rows if r["cls"] == c]
        P("   %-20s R10 admits %2d/%d, R120 admits %2d/%d" % (c, sum(r["admit_R10"] for r in rs), len(rs), sum(r["admit_R120"] for r in rs), len(rs)))

    # sabotage detail
    P("")
    P("== sabotage: smallest failing change (per pair) ==")
    for c, nm in [("sabotage_scale_min", "readout scaled by alpha: relative change |1-alpha|"), ("sabotage_noise_min", "readout + sigma*D: sigma/std(W3_p)")]:
        rs = [r for r in rows if r["cls"] == c]
        sz = [r["size"] for r in rs]
        P("%s: n=%d of %d pairs (benign failing ground truth excluded) ; %s: mean %.3f min %.3f max %.3f ; grid non-monotone in %d pairs" %
          (c, len(rs), N_PAIRS, nm, np.mean(sz), np.min(sz), np.max(sz), sum(r.get("nonmonotone_grid", 0) for r in rs)))
        P("   at that point: novel R2 mean %.4f, native R2 drop mean %.4f; drift mean %.4f; agree mean %.4f; admitted %d/%d" %
          (np.mean([r["nov_r2"] for r in rs]), np.mean([r["base_r2"] - r["nat_r2"] for r in rs]),
           np.mean([r["native_drift"] for r in rs]), np.mean([r["donor_agree"] for r in rs]), sum(r["admit"] for r in rs), len(rs)))
    P("")
    P("== sabotage sweeps (grid points only, mean over pairs) ==")
    for kind, grid in [("scale", SCALE_GRID), ("noise", NOISE_GRID)]:
        P("kind %s: size | n | drift mean | agree mean | admitted | GT-pass | nov R2 mean | nat R2 mean" % kind)
        for s in grid:
            ss = [x for x in sweeps if x["kind"] == kind and x["phase"] == "grid" and x["size"] == s]
            P("   %5.2f | %d | %.4f | %.4f | %2d/%d | %2d/%d | %.4f | %.4f" % (
                s, len(ss), np.mean([x["native_drift"] for x in ss]), np.mean([x["donor_agree"] for x in ss]),
                sum(x["admit"] for x in ss), len(ss), sum(x["gt_pass"] for x in ss), len(ss),
                np.mean([x["nov_r2"] for x in ss]), np.mean([x["nat_r2"] for x in ss])))

    # stale
    rs = [r for r in rows if r["cls"] == "stale_donor"]
    P("")
    P("stale donor (40 steps): its shifted novel R2 mean %.4f (full donor %.4f); graft novel R2 mean %.4f; agreement vs its own donor mean %.4f; vs reference donor mean %.4f (min %.4f)" %
      (np.mean([r["stale_donor_novel_r2"] for r in rs]), np.mean([r["donor_novel_r2"] for r in nb]), np.mean([r["nov_r2"] for r in rs]),
       np.mean([r["donor_agree"] for r in rs]), np.mean([r["agree_vs_reference_donor"] for r in rs]), np.min([r["agree_vs_reference_donor"] for r in rs])))
    P("total wall time %.0fs" % (time.time() - t_start))

    json.dump(dict(rule=rule, rows=rows, sweeps=sweeps, class_table=classtab, confusion=conf, auroc=au, exposures=exposures,
                   seeds={r["pair"]: r["seeds"] for r in results}, pair_seconds=[r["seconds"] for r in results]),
              open(os.path.join(HERE, "admission_oos.json"), "w"), indent=1, default=float)
    open(os.path.join(HERE, "admission_oos.out"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
