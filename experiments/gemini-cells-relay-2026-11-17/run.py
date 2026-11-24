#!/usr/bin/env python3
"""Run the gemini-cells relay. Live commands spend money; the ledger enforces the cap.

    python3 run.py calibrate --root R --harness seed --calls 5 --n 6
    python3 run.py exam --root R --harness seed --label seed --repeats 4
    python3 run.py aa --root R --n 6
    python3 run.py arm twin-free-collective --rep 0 --root R
    python3 run.py block --root R --reps 4 --jobs 5
    python3 run.py assay --root R
    python3 run.py assay2 --root R2 --tag partA --approval APPROVAL.json   (block 2, see block2/PLAN.md)

Needs root on Linux (the sandbox) and the `claude` command line tool signed in.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from referee import relay  # noqa: E402
from referee.bench import Bench, Store  # noqa: E402
from referee.brain import ClaudeCLI, Ledger, SpendCapReached  # noqa: E402

CAP_USD = 25.0
REPLICATE_RESERVE_USD = 5.0   # a replicate (five runs) starts only if this much is left under the cap


def backend(root: Path, model: str):
    return ClaudeCLI(model, Ledger(Path(root) / "spend.json", CAP_USD))


def families():
    from referee import tasks
    return tasks.FAMILIES


def cmd_calibrate(a) -> None:
    """Score one harness on fresh instances of every family, several repeats."""
    cfg = relay.Config()
    root = Path(a.root)
    b = Bench(root / "calib-scratch", backend(root, cfg.model), families(), parallel=a.parallel)
    harness = HERE / a.harness if not Path(a.harness).is_absolute() else Path(a.harness)
    fams = a.families.split(",") if a.families else list(cfg.families + cfg.heldout)
    inst = [(f, a.seed_base + i) for f in fams for i in range(a.n)]
    t0 = time.time()
    r = b.benchmark(harness, inst, level=a.level, calls=a.calls,
                    prompt_chars=cfg.episode_prompt_chars, wall_s=cfg.episode_wall_s)
    row = {"kind": "calibrate", "harness": a.harness, "calls_cap": a.calls, "level": a.level,
           "n_per_family": a.n, "seed_base": a.seed_base, "mean": r["mean"],
           "by_family": r["by_family"], "calls": r["calls"], "usd": r["usd"],
           "wall_s": round(time.time() - t0, 1),
           "episodes": [{k: e[k] for k in ("family", "seed", "score", "calls", "rc", "wall_s")}
                        for e in r["episodes"]]}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as f:
        f.write(json.dumps(row) + "\n")
    if a.traces:
        td = Path(a.traces)
        td.mkdir(parents=True, exist_ok=True)
        for i, e in enumerate(r["episodes"]):
            (td / f"{e['family']}_{e['seed']}_{e['score']:.2f}.txt").write_text(e["trace"])
    for f in fams:
        sc = [e["score"] for e in r["episodes"] if e["family"] == f]
        print(f"{f:8s} mean {statistics.mean(sc):.3f} sd {statistics.pstdev(sc):.3f} "
              f"calls {statistics.mean(e['calls'] for e in r['episodes'] if e['family'] == f):.1f} {sc}")
    print(f"all mean {r['mean']:.3f} calls {r['calls']} usd {r['usd']:.4f} wall {row['wall_s']}s")


def cmd_exam(a) -> None:
    """Sit one harness through the final exam several times. Writes results/<label>_exam.json."""
    cfg = relay.Config()
    root = Path(a.root)
    b = Bench(root / "exam-scratch" / a.label, backend(root, cfg.model), families(), parallel=a.parallel)
    harness = HERE / a.harness
    inst = relay.exam_instances(cfg)
    out = {"label": a.label, "harness": a.harness, "repeats": a.repeats, "calls_cap": cfg.episode_calls,
           "level": cfg.level, "visible": [], "heldout": [], "by_family": [], "calls": 0, "usd": 0.0,
           "model_errors": 0, "episodes": []}
    for i in range(a.repeats):
        r = b.benchmark(harness, inst, level=cfg.level, calls=cfg.episode_calls,
                        prompt_chars=cfg.episode_prompt_chars, wall_s=cfg.episode_wall_s)
        vis = [e["score"] for e in r["episodes"] if e["family"] in cfg.families]
        held = [e["score"] for e in r["episodes"] if e["family"] in cfg.heldout]
        out["visible"].append(round(statistics.mean(vis), 4))
        out["heldout"].append(round(statistics.mean(held), 4))
        out["by_family"].append(r["by_family"])
        out["calls"] += r["calls"]
        out["usd"] = round(out["usd"] + r["usd"], 4)
        out["model_errors"] += r["model_errors"]
        out["episodes"].append([{k: e[k] for k in ("family", "seed", "score", "calls")} for e in r["episodes"]])
        print(a.label, "repeat", i, "visible", out["visible"][-1], "heldout", out["heldout"][-1], flush=True)
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / f"{a.label}_exam.json").write_text(json.dumps(out, indent=1))


def cmd_aa(a) -> None:
    """Gate noise with nothing changed: the seed against itself on the same fresh tasks."""
    cfg = relay.Config()
    root = Path(a.root)
    b = Bench(root / "aa-scratch", backend(root, cfg.model), families(), parallel=a.parallel)
    rows = []
    for i in range(a.n):
        inst = relay.instances(f"aa|{a.salt}|{i}", 0, cfg.families, cfg.per_family)
        x = b.benchmark(relay.SEED_DIR, inst, level=cfg.level, calls=cfg.episode_calls,
                        prompt_chars=cfg.episode_prompt_chars, wall_s=cfg.episode_wall_s)
        y = b.benchmark(relay.SEED_DIR, inst, level=cfg.level, calls=cfg.episode_calls,
                        prompt_chars=cfg.episode_prompt_chars, wall_s=cfg.episode_wall_s)
        rows.append({"i": i, "first": x["mean"], "second": y["mean"], "diff": round(y["mean"] - x["mean"], 4),
                     "kept_by_gate": y["mean"] >= x["mean"] - cfg.margin, "usd": round(x["usd"] + y["usd"], 4),
                     "calls": x["calls"] + y["calls"]})
        print(rows[-1], flush=True)
    diffs = [r["diff"] for r in rows]
    out = {"n": a.n, "margin": cfg.margin, "rows": rows, "mean_diff": round(statistics.mean(diffs), 4),
           "sd_diff": round(statistics.stdev(diffs), 4) if len(diffs) > 1 else None,
           "kept": sum(r["kept_by_gate"] for r in rows)}
    (HERE / "results" / "gate_noise.json").write_text(json.dumps(out, indent=1))
    print({k: out[k] for k in ("mean_diff", "sd_diff", "kept")})


def cmd_resit(a) -> None:
    """Sit the final harnesses of one finished run through the exam again. Used when the
    model backend failed during a run's exam. Writes <run>/exam_resit.jsonl; nothing else
    of the run is touched."""
    cfg = relay.Config()
    root = Path(a.root)
    run_dir = root / "runs" / a.run
    rows = [json.loads(x) for x in (run_dir / "log.jsonl").read_text().splitlines()]
    end = next(x for x in rows if x["kind"] == "end")
    r = relay.Relay("twin-free-collective", 0, cfg, root / "rs" / a.run[-12:], backend(root, cfg.model), families())
    out, done = [], {}
    for slot in ("A", "B"):
        h = end["harness"][slot]
        if h not in done:
            hh = r.store.put(Store(run_dir).path(h))
            assert hh == h
            done[h] = r._slim(r._bm(h, relay.exam_instances(cfg)))
        out.append({"kind": "exam", "slot": slot, "harness": h, "report": done[h], "resit": True,
                    "why": a.why})
        print(a.run, slot, done[h]["mean"], "model errors", done[h]["model_errors"], flush=True)
    (run_dir / "exam_resit.jsonl").write_text("".join(json.dumps(x) + "\n" for x in out))


def cmd_arm(a) -> None:
    cfg = relay.Config()
    root = Path(a.root)
    r = relay.Relay(a.arm, a.rep, cfg, root / "runs", backend(root, cfg.model), families())
    if (r.dir / "log.jsonl").exists():
        print(f"{r.run_id}: a log exists already, not rerunning")
        return
    print(json.dumps(r.run()))


def cmd_block(a) -> None:
    """Run the block replicate by replicate: the five arms of a replicate side by side, and the
    next replicate only when they have all finished and the reserve is still there."""
    jobs = [(arm, rep) for rep in range(a.reps) for arm in relay.ARMS]
    running: list[tuple[subprocess.Popen, str]] = []
    logdir = Path(a.root) / "stdout"
    logdir.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(Path(a.root) / "spend.json", CAP_USD)
    started_reps: set[int] = set()
    while jobs or running:
        while jobs and len(running) < a.jobs:
            arm, rep = jobs[0]
            if rep not in started_reps:
                if running:        # a replicate starts only when the one before it has finished
                    break
                spent = ledger.read().get("usd", 0.0)
                if spent > CAP_USD - REPLICATE_RESERVE_USD:
                    print(f"replicate {rep} not started: {spent:.2f} dollars spent, reserve is "
                          f"{REPLICATE_RESERVE_USD}", flush=True)
                    jobs = []
                    break
                started_reps.add(rep)
            jobs.pop(0)
            f = open(logdir / f"{arm}-r{rep}.txt", "w")
            p = subprocess.Popen([sys.executable, str(HERE / "run.py"), "arm", arm, "--rep", str(rep),
                                  "--root", a.root], stdout=f, stderr=subprocess.STDOUT)
            running.append((p, f"{arm}-r{rep}"))
            print("started", f"{arm}-r{rep}", flush=True)
        time.sleep(5)
        for p, name in list(running):
            if p.poll() is not None:
                running.remove((p, name))
                print("finished", name, "rc", p.returncode, flush=True)


def cmd_assay(a) -> None:
    """Builder assay: each run's final harness (slot A) takes one build turn on a fresh seed
    harness, with the collective brief. The paired gain of its candidate over the seed is a
    direct measure of how good a builder that harness makes its cell."""
    cfg = relay.Config()
    root = Path(a.root)
    out = root / f"assay-{a.shard.replace('/', 'of')}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(x)["run"] + "|" + json.loads(x)["slot"] for x in out.read_text().splitlines()}
    shard, of = (int(x) for x in a.shard.split("/"))
    # replicate by replicate, so that a short budget leaves whole replicates covered
    order = sorted((root / "runs").iterdir(), key=lambda d: (d.name.rsplit("-r", 1)[-1].zfill(3), d.name))
    for i, run_dir in enumerate(order):
        if i % of != shard:
            continue
        if not (run_dir / "log.jsonl").exists():
            continue
        rows = [json.loads(x) for x in (run_dir / "log.jsonl").read_text().splitlines()]
        end = [x for x in rows if x["kind"] == "end"]
        if not end:
            continue
        for slot in a.slots.split(","):
            key = run_dir.name + "|" + slot
            if key in done:
                continue
            # a short scratch path: a Unix socket path may hold about 100 characters
            r = relay.Relay("twin-free-collective", 0, cfg, root / "as" / f"{i:02d}{slot}",
                            backend(root, cfg.model), families())
            r.run_id = f"assay|{run_dir.name}|{slot}"
            seed_h = r.store.put(relay.SEED_DIR)
            src = Store(run_dir).path(end[0]["harness"][slot])
            builder_h = r.store.put(src)
            # the same information a first-turn builder gets: a fresh benchmark report of the seed
            try:
                base = r._bm(seed_h, relay.instances(f"{r.secret}|base|B", 0, cfg.families, cfg.per_family))
                ev = r.build_turn(1, "A", "B", builder_h, seed_h, seed_h, base,
                                  {"A": base["mean"], "B": base["mean"]}, [])
            except SpendCapReached:
                print("spend cap reached: the assay stops at", run_dir.name, flush=True)
                return
            ev.pop("_cand_report", None), ev.pop("_inc_report", None)
            ev["builder_is_seed"] = builder_h == seed_h
            ev.update(kind="assay", run=run_dir.name, slot=slot, usd=round(r.usd, 4))
            with open(out, "a") as f:
                f.write(json.dumps(ev) + "\n")
            print(run_dir.name, slot, ev["outcome"], ev.get("inc"), ev.get("cand"), flush=True)


PLAN_FILE = HERE / "block2" / "PLAN.md"


def check_approval(path: str | None, tag: str) -> float:
    """Block 2's live commands start only with an approval file bound to the exact plan text
    and run tag: {"plan_sha256": ..., "tag": ..., "cap_usd": ...}. Returns the cap."""
    if not path:
        raise SystemExit("refused: a live block-2 command needs --approval (see block2/PLAN.md)")
    try:
        approval = json.loads(Path(path).read_text())
        cap = float(approval["cap_usd"])
    except Exception as exc:
        raise SystemExit(f"refused: unreadable approval file ({exc})")
    want = hashlib.sha256(PLAN_FILE.read_bytes()).hexdigest()
    if approval.get("plan_sha256") != want:
        raise SystemExit("refused: the approval is for another text of block2/PLAN.md")
    if approval.get("tag") != tag:
        raise SystemExit(f"refused: the approval is for run tag {approval.get('tag')!r}, not {tag!r}")
    if not 0 < cap <= 50:
        raise SystemExit("refused: cap_usd must be above 0 and at most 50")
    return cap


def assay2_plan(sources: list[str], slots: list[str], reps: int, seed_reps: int) -> list[tuple]:
    """The order of block 2's assays: repeat by repeat, so that a run cut short leaves every
    harness with the same number of assays give or take one. Rows are (rep, run, slot);
    run None is the seed harness as builder."""
    plan = []
    for rep in range(max(reps, seed_reps)):
        if rep < reps:
            plan += [(rep, run, slot) for run in sources for slot in slots]
        if rep < seed_reps:
            plan.append((rep, None, "seed"))
    return plan


def cmd_assay2(a) -> None:
    """Block 2, part A: fresh builder assays of the pilot's final harnesses, read from the
    record's packed archives, plus the seed harness as a builder. Same procedure as `assay`,
    on new seeds, with both slots and several repeats. Refuses to start without an approval."""
    import tarfile
    cap = check_approval(a.approval, a.tag)
    cfg = relay.Config()
    root = Path(a.root)
    src_root = root / "src"
    sources = []
    for run_dir in sorted(Path(a.source).iterdir()):
        archive = run_dir / "artifacts.tar.gz"
        if not archive.is_file():
            continue
        dest = src_root / run_dir.name
        if not dest.is_dir():
            dest.mkdir(parents=True)
            with tarfile.open(archive) as tf:
                tf.extractall(dest, filter="data")
            (dest / "log.jsonl").write_bytes((run_dir / "log.jsonl").read_bytes())
        sources.append(run_dir.name)
    ledger = Ledger(root / "spend.json", cap)
    be = ClaudeCLI(cfg.model, ledger)
    out = root / f"assay2-{a.tag}-{a.shard.replace('/', 'of')}.jsonl"
    done = set()
    if out.exists():
        done = {(r["rep"], r["run"], r["slot"]) for r in map(json.loads, out.read_text().splitlines())}
    shard, of = (int(x) for x in a.shard.split("/"))
    plan = assay2_plan(sources, a.slots.split(","), a.reps, a.seed_reps)
    for i, (rep, run, slot) in enumerate(plan):
        if i % of != shard or (rep, run, slot) in done:
            continue
        r = relay.Relay("twin-free-collective", 0, cfg, root / "as" / f"{i:03d}", be, families())
        r.run_id = f"assay2|{a.tag}|{run}|{slot}|{rep}"
        seed_h = r.store.put(relay.SEED_DIR)
        if run is None:
            builder_h = seed_h
        else:
            rows = [json.loads(x) for x in (src_root / run / "log.jsonl").read_text().splitlines()]
            end = [x for x in rows if x["kind"] == "end"][0]
            builder_h = r.store.put(Store(src_root / run).path(end["harness"][slot]))
        try:
            base = r._bm(seed_h, relay.instances(f"{r.secret}|base|B", 0, cfg.families, cfg.per_family))
            ev = r.build_turn(1, "A", "B", builder_h, seed_h, seed_h, base,
                              {"A": base["mean"], "B": base["mean"]}, [])
        except SpendCapReached:
            print("spend cap reached: part A stops at row", i, flush=True)
            return
        ev.pop("_cand_report", None), ev.pop("_inc_report", None)
        ev.update(kind="assay2", tag=a.tag, rep=rep, run=run, slot=slot, builder_is_seed=builder_h == seed_h,
                  secret=r.secret, usd=round(r.usd, 4))
        with open(out, "a") as f:
            f.write(json.dumps(ev) + "\n")
        print(run, slot, rep, ev["outcome"], ev.get("inc"), ev.get("cand"), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibrate")
    c.add_argument("--root", required=True)
    c.add_argument("--harness", default="seed")
    c.add_argument("--calls", type=int, default=5)
    c.add_argument("--level", type=int, default=2)
    c.add_argument("--n", type=int, default=6)
    c.add_argument("--seed-base", type=int, default=500000)
    c.add_argument("--families", default="")
    c.add_argument("--parallel", type=int, default=10)
    c.add_argument("--out", default=str(HERE / "results" / "calibration.jsonl"))
    c.add_argument("--traces", default="")
    c.set_defaults(fn=cmd_calibrate)
    e = sub.add_parser("exam")
    e.add_argument("--root", required=True)
    e.add_argument("--harness", default="seed")
    e.add_argument("--label", default="seed")
    e.add_argument("--repeats", type=int, default=4)
    e.add_argument("--parallel", type=int, default=10)
    e.set_defaults(fn=cmd_exam)
    g = sub.add_parser("aa")
    g.add_argument("--root", required=True)
    g.add_argument("--n", type=int, default=6)
    g.add_argument("--salt", default="0")
    g.add_argument("--parallel", type=int, default=10)
    g.set_defaults(fn=cmd_aa)
    t = sub.add_parser("resit")
    t.add_argument("--root", required=True)
    t.add_argument("--run", required=True)
    t.add_argument("--why", required=True)
    t.set_defaults(fn=cmd_resit)
    r = sub.add_parser("arm")
    r.add_argument("arm", choices=sorted(relay.ARMS))
    r.add_argument("--rep", type=int, required=True)
    r.add_argument("--root", required=True)
    r.set_defaults(fn=cmd_arm)
    b = sub.add_parser("block")
    b.add_argument("--root", required=True)
    b.add_argument("--reps", type=int, default=4)
    b.add_argument("--jobs", type=int, default=5)
    b.set_defaults(fn=cmd_block)
    s = sub.add_parser("assay")
    s.add_argument("--root", required=True)
    s.add_argument("--slots", default="A")
    s.add_argument("--shard", default="0/1", help="i/n: take every n-th run, starting at i")
    s.set_defaults(fn=cmd_assay)
    s2 = sub.add_parser("assay2")
    s2.add_argument("--root", required=True)
    s2.add_argument("--source", default=str(HERE / "results" / "runs"))
    s2.add_argument("--tag", required=True)
    s2.add_argument("--approval")
    s2.add_argument("--slots", default="A,B")
    s2.add_argument("--reps", type=int, default=3)
    s2.add_argument("--seed-reps", type=int, default=12)
    s2.add_argument("--shard", default="0/1", help="i/n: take every n-th row of the plan, starting at i")
    s2.set_defaults(fn=cmd_assay2)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
