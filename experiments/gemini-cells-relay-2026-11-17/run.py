#!/usr/bin/env python3
"""Run the gemini-cells relay. Live commands spend money; the ledger enforces the cap.

    python3 run.py calibrate --root R --harness seed --calls 5 --n 6
    python3 run.py arm twin-free-collective --rep 0 --root R
    python3 run.py block --root R --reps 3 --jobs 4
    python3 run.py assay --root R

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
from referee.brain import ClaudeCLI, Ledger  # noqa: E402

CAP_USD = 25.0


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


def cmd_arm(a) -> None:
    cfg = relay.Config()
    root = Path(a.root)
    r = relay.Relay(a.arm, a.rep, cfg, root / "runs", backend(root, cfg.model), families())
    if (r.dir / "log.jsonl").exists():
        print(f"{r.run_id}: a log exists already, not rerunning")
        return
    print(json.dumps(r.run()))


def cmd_block(a) -> None:
    """Run every arm for each replicate, interleaved, a few runs at a time."""
    jobs = [(arm, rep) for rep in range(a.reps) for arm in relay.ARMS]
    running: list[tuple[subprocess.Popen, str]] = []
    logdir = Path(a.root) / "stdout"
    logdir.mkdir(parents=True, exist_ok=True)
    while jobs or running:
        while jobs and len(running) < a.jobs:
            arm, rep = jobs.pop(0)
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
    out = root / "assay.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(x)["run"] + "|" + json.loads(x)["slot"] for x in out.read_text().splitlines()}
    for run_dir in sorted((root / "runs").iterdir()):
        rows = [json.loads(x) for x in (run_dir / "log.jsonl").read_text().splitlines()]
        end = [x for x in rows if x["kind"] == "end"]
        if not end:
            continue
        for slot in a.slots.split(","):
            key = run_dir.name + "|" + slot
            if key in done:
                continue
            r = relay.Relay("twin-free-collective", 0, cfg, root / "assay-scratch" / run_dir.name / slot,
                            backend(root, cfg.model), families())
            r.run_id = f"assay|{run_dir.name}|{slot}"
            seed_h = r.store.put(relay.SEED_DIR)
            src = Store(run_dir).path(end[0]["harness"][slot])
            builder_h = r.store.put(src)
            ev = r.build_turn(1, "A", "B", builder_h, seed_h, seed_h, None, {"A": 0.0, "B": 0.0}, [])
            ev.pop("_cand_report", None), ev.pop("_inc_report", None)
            ev.update(kind="assay", run=run_dir.name, slot=slot, usd=round(r.usd, 4))
            with open(out, "a") as f:
                f.write(json.dumps(ev) + "\n")
            print(run_dir.name, slot, ev["outcome"], ev.get("inc"), ev.get("cand"), flush=True)


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
    r = sub.add_parser("arm")
    r.add_argument("arm", choices=sorted(relay.ARMS))
    r.add_argument("--rep", type=int, required=True)
    r.add_argument("--root", required=True)
    r.set_defaults(fn=cmd_arm)
    b = sub.add_parser("block")
    b.add_argument("--root", required=True)
    b.add_argument("--reps", type=int, default=3)
    b.add_argument("--jobs", type=int, default=4)
    b.set_defaults(fn=cmd_block)
    s = sub.add_parser("assay")
    s.add_argument("--root", required=True)
    s.add_argument("--slots", default="A")
    s.set_defaults(fn=cmd_assay)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
