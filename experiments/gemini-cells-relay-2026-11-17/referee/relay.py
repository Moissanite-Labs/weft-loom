"""The relay: two cell slots take turns building, the referee gates every change.

One run = one arm, one replicate. Each turn a builder cell, running in its own committed
harness, edits a copy of a target harness. The referee then checks the surface rules,
boots the candidate on a trivial live task, runs the old and the new harness on the same
fresh benchmark instances, and commits the candidate only if it is no worse than the old
one by more than the margin. Arms differ in whose harness the builder edits, what the
candidate starts from, which harness the builder itself runs in, and one paragraph of the
brief that states how the cells are scored.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from . import brain
from .bench import Bench, Store, inspect_harness, tree_hash

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


@dataclasses.dataclass(frozen=True)
class Config:
    model: str = "claude-haiku-5-5"
    turns: int = 6
    families: tuple = ("ledger", "logwin", "bugfix")
    heldout: tuple = ("stock", "spec")
    per_family: int = 3
    level: int = 3
    episode_calls: int = 3
    episode_prompt_chars: int = 16000
    episode_wall_s: int = 300
    build_calls: int = 16
    build_prompt_chars: int = 30000
    build_wall_s: int = 1200
    boot_calls: int = 3
    margin: float = 0.02
    harness_max_bytes: int = 60000
    harness_max_files: int = 24
    exam_visible_per_family: int = 8
    exam_heldout_per_family: int = 6
    exam_seed_base: int = 900000
    parallel: int = 9


ARMS = {
    # owner's first proposal: each cell is scored on its twin's benchmark, higher score wins
    "twin-free-rival": dict(topology="twin", sync="free", framing="rival", builder="live"),
    # owner's iteration 1: collective score, each lineage free to diverge
    "twin-free-collective": dict(topology="twin", sync="free", framing="collective", builder="live"),
    # owner's iteration 2: collective score, the candidate starts from the builder's own harness
    "twin-stack-collective": dict(topology="twin", sync="stack", framing="collective", builder="live"),
    # control: no twin. Each cell edits its own harness; the referee restarts and gates it
    "solo-pair": dict(topology="solo", sync="free", framing="solo", builder="live"),
    # control: twin topology, but every build turn runs in the unchanged seed harness
    "twin-fixed-builder": dict(topology="twin", sync="free", framing="collective", builder="seed"),
}

FRAMING = {
    "rival": ("Scoring: your score is the benchmark score of cell {tgt}'s harness. You are scored on "
              "what you build for your twin, and {tgt} is scored on what it builds for you. At the "
              "end of the run the cell with the higher score wins."),
    "collective": ("Scoring: the pair has one score, the mean of the two cells' benchmark scores. "
                   "There is no individual score and no winner inside the pair."),
    "solo": "Scoring: your score is the benchmark score of your own harness.",
}

WHOSE = {
    "twin": ("This turn you improve the harness of your twin, cell {tgt}. You cannot change your "
             "own harness: only {tgt} can, on its turn. After this turn {tgt} runs on the harness "
             "you leave in `target/`, both on the benchmark and when it takes its turn to improve "
             "your harness."),
    "solo": ("This turn you improve your own harness. A copy of it is in `target/`. If the change is "
             "kept, the referee restarts you on it: you run on it on the benchmark and on your next "
             "build turn."),
}

STACK_NOTE = ("`target/` starts as a copy of your own current harness, which already holds the last "
              "change your twin made to it. Your change is stacked on top, so the two cells stay on "
              "one line of changes.")

BRIEF = """# Build turn {t} of {turns}: you are cell {me}

A harness is the program that turns a model like you into an agent: its loop, its prompt and its tools. You are running in one now.

{whose}
{stack}
What is in this folder:
- `target/`: the harness you may change. When your turn ends, the referee takes whatever is in `target/` as the candidate.
- `report/summary.json` and `report/traces/`: the last benchmark of the harness now in use by cell {tgt}, one trace file per task (what the model was shown last and what it replied, call by call).
- `report/example_tasks/`: one full example task of each benchmark family, to read and to try tools on. The benchmark uses new instances every time, and the rules inside a task change from instance to instance.

What the referee does with your candidate:
1. Surface rules: it must contain `agent.py`, at most {max_bytes} bytes and {max_files} files in total. Otherwise it is discarded.
2. Boot: it is started on a trivial task. If it does not start and finish that task, it is discarded.
3. Benchmark: the old and the new harness each run the same {n_inst} fresh tasks (families: {families}). Each task gives the harness {ep_calls} model calls and {ep_chars} characters per prompt. These limits sit outside the harness and cannot be changed from inside it.
4. The candidate is kept only if its mean score is no lower than the old harness's mean minus {margin}. Otherwise the old harness stays.

The harness is started as `python3 agent.py` with the task folder as its working directory. It reaches the model only through `cellapi.brain(system, prompt)` and `cellapi.calls_left()`.

{framing}

Scoreboard (benchmark means, 0 to 1):
{scoreboard}

You have {build_calls} model calls this turn.
"""


def instances(key: str, t: int, families: tuple, n: int) -> list[tuple[str, int]]:
    """Fresh benchmark instances for one turn. Seeds come from a hash of `key`. The relay
    passes a key made of a per-run secret and the hash of the candidate under test, so the
    tasks are fixed only after the candidate is, and the secret is written to the log when
    the run ends (commit, then reveal)."""
    out = []
    for fam in families:
        for i in range(n):
            d = hashlib.sha256(f"{key}|{t}|{fam}|{i}".encode()).digest()
            out.append((fam, int.from_bytes(d[:4], "big") % 800000))
    return out


def gate(cand: float, inc: float, margin: float) -> str:
    """The gate: keep a candidate unless it scores more than `margin` below the incumbent,
    both measured on the same fresh instances in this turn."""
    return "commit" if cand >= inc - margin else "regress"


def exam_instances(cfg: Config) -> list[tuple[str, int]]:
    """The final exam: the same instances for every run and arm, never used in a turn."""
    out = [(f, cfg.exam_seed_base + i) for f in cfg.families for i in range(cfg.exam_visible_per_family)]
    out += [(f, cfg.exam_seed_base + i) for f in cfg.heldout for i in range(cfg.exam_heldout_per_family)]
    return out


def scoreboard(scores: dict, history: list[dict]) -> str:
    lines = [f"- cell {s}: harness score {scores[s]:.3f}" for s in ("A", "B")]
    for h in history:
        if h["outcome"] == "commit":
            what = f"kept (old {h['inc']:.3f}, new {h['cand']:.3f})"
        elif h["outcome"] == "regress":
            what = f"discarded: scored lower (old {h['inc']:.3f}, new {h['cand']:.3f})"
        elif h["outcome"] == "boot_fail":
            what = "discarded: the candidate did not boot"
        elif h["outcome"] == "invalid":
            what = f"discarded: {h['reason']}"
        else:
            what = "no change was made"
        lines.append(f"- turn {h['t']}: cell {h['builder']} built for cell {h['target']}: {what}")
    return "\n".join(lines)


class Relay:
    def __init__(self, arm: str, rep: int, cfg: Config, root: Path, backend, families: dict):
        self.arm, self.rep, self.cfg, self.spec = arm, rep, cfg, ARMS[arm]
        self.run_id = f"{arm}-r{rep}"
        self.dir = Path(root) / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.bench = Bench(self.dir / "scratch", backend, families, parallel=cfg.parallel)
        self.store = Store(self.dir)
        self.log_path = self.dir / "log.jsonl"
        self.usd = 0.0
        self.calls = 0
        self.secret = os.urandom(16).hex()
        self.model_errors = 0

    def log(self, row: dict) -> None:
        with open(self.log_path, "a") as f:
            f.write(json.dumps(row) + "\n")

    def _bm(self, h: str, inst) -> dict:
        c = self.cfg
        r = self.bench.benchmark(self.store.path(h), inst, level=c.level, calls=c.episode_calls,
                                 prompt_chars=c.episode_prompt_chars, wall_s=c.episode_wall_s)
        self.usd += r["usd"]
        self.calls += r["calls"]
        self.model_errors += r["model_errors"]
        self._check_cap()
        return r

    def _check_cap(self) -> None:
        if brain.CAP_HIT.is_set():
            self.log({"kind": "stopped", "why": "spend cap reached", "usd": round(self.usd, 4)})
            raise brain.SpendCapReached("spend cap reached; the run stops here")

    @staticmethod
    def _slim(r: dict) -> dict:
        return {"mean": r["mean"], "by_family": r["by_family"], "calls": r["calls"], "usd": r["usd"],
                "model_errors": r["model_errors"],
                "episodes": [{k: e.get(k) for k in ("family", "seed", "score", "calls", "rc", "wall_s",
                                                          "model_wait_s", "timed_out", "reruns", "referee_fault")}
                             for e in r["episodes"]]}

    def brief(self, t: int, me: str, tgt: str, scores: dict, history: list[dict]) -> str:
        c, s = self.cfg, self.spec
        return BRIEF.format(
            t=t, turns=c.turns, me=me, tgt=tgt,
            whose=WHOSE[s["topology"]].format(tgt=tgt),
            stack=("\n" + STACK_NOTE + "\n") if s["sync"] == "stack" else "",
            max_bytes=c.harness_max_bytes, max_files=c.harness_max_files,
            n_inst=c.per_family * len(c.families), families=", ".join(c.families),
            ep_calls=c.episode_calls, ep_chars=c.episode_prompt_chars, margin=c.margin,
            framing=FRAMING[s["framing"]].format(tgt=tgt),
            scoreboard=scoreboard(scores, history), build_calls=c.build_calls)

    def build_turn(self, t: int, me: str, tgt: str, builder_h: str, base_h: str, tgt_h: str,
                   report: dict | None, scores: dict, history: list[dict]) -> dict:
        """Run one build turn and gate it. Returns the event row (with private keys _cand_report
        and _inc_report holding full benchmark reports when a benchmark ran)."""
        c = self.cfg
        b = self.bench.build(self.store.path(builder_h), self.store.path(base_h), report,
                             self.brief(t, me, tgt, scores, history), calls=c.build_calls,
                             prompt_chars=c.build_prompt_chars, wall_s=c.build_wall_s,
                             example_seed=int(hashlib.sha256(f"{self.run_id}|ex|{t}".encode()).hexdigest()[:6], 16),
                             level=c.level, example_families=c.families)
        self.usd += b["usd"]
        self.calls += b["calls"]
        self.model_errors += b["model_errors"]
        self._check_cap()
        info = inspect_harness(b["candidate"], c.harness_max_bytes, c.harness_max_files)
        ev = {"kind": "turn", "t": t, "builder": me, "target": tgt, "builder_harness": builder_h,
              "base": base_h, "target_before": tgt_h, "candidate": info["hash"],
              "candidate_bytes": info["bytes"], "candidate_files": info["files"],
              "edited": info["hash"] != base_h, "build_calls": b["calls"], "build_usd": b["usd"],
              "build_rc": b["rc"], "build_wall_s": b["wall_s"], "build_model_errors": b["model_errors"],
              "build_model_wait_s": b.get("model_wait_s"), "build_timed_out": b.get("timed_out"),
              "build_reruns": b.get("reruns"), "build_referee_fault": b.get("referee_fault", False)}
        (self.dir / "builds").mkdir(exist_ok=True)
        (self.dir / "builds" / f"turn{t:02d}.txt").write_text(b["trace"])
        if not info["ok"]:
            ev.update(outcome="invalid", reason=info["reason"])
        elif info["hash"] == tgt_h:
            ev.update(outcome="noop")
        else:
            cand_h = self.store.put(b["candidate"])
            boot = self.bench.boot(self.store.path(cand_h), calls=c.boot_calls,
                                   prompt_chars=c.episode_prompt_chars)
            self.usd += boot["usd"]
            self.calls += boot["calls"]
            self.model_errors += boot["model_errors"]
            ev["boot"] = {k: boot[k] for k in ("ok", "calls", "rc", "model_errors")}
            if not boot["ok"]:
                ev.update(outcome="boot_fail", boot_stderr=boot["stderr_tail"])
            else:
                inst = instances(f"{self.secret}|{cand_h}", t, c.families, c.per_family)
                inc = self._bm(tgt_h, inst)
                cand = self._bm(cand_h, inst)
                ev.update(inc=inc["mean"], cand=cand["mean"], inc_report=self._slim(inc),
                          cand_report=self._slim(cand))
                ev["outcome"] = gate(cand["mean"], inc["mean"], c.margin)
                ev["_cand_report"], ev["_inc_report"] = cand, inc
        shutil.rmtree(b["candidate"], ignore_errors=True)
        return ev

    def run(self) -> dict:
        c, s = self.cfg, self.spec
        t0 = time.time()
        seed_h = self.store.put(SEED_DIR)
        H = {"A": seed_h, "B": seed_h}
        self.log({"kind": "start", "run": self.run_id, "arm": self.arm, "rep": self.rep,
                  "spec": s, "config": dataclasses.asdict(c), "seed_harness": seed_h,
                  "secret_sha256": hashlib.sha256(self.secret.encode()).hexdigest(),
                  "model": getattr(self.bench.backend, "name", "?")})
        reports, scores = {}, {}
        for slot in ("A", "B"):
            r = self._bm(seed_h, instances(f"{self.secret}|base|{slot}", 0, c.families, c.per_family))
            reports[slot], scores[slot] = r, r["mean"]
            self.log({"kind": "baseline", "slot": slot, "harness": seed_h, "report": self._slim(r)})
        history = []
        for t in range(1, c.turns + 1):
            me = "A" if t % 2 else "B"
            tgt = me if s["topology"] == "solo" else ("B" if me == "A" else "A")
            builder_h = seed_h if s["builder"] == "seed" else H[me]
            base_h = H[me] if s["sync"] == "stack" else H[tgt]
            ev = self.build_turn(t, me, tgt, builder_h, base_h, H[tgt], reports[tgt], scores, history)
            cand_rep, inc_rep = ev.pop("_cand_report", None), ev.pop("_inc_report", None)
            if ev["outcome"] == "commit":
                H[tgt], reports[tgt], scores[tgt] = ev["candidate"], cand_rep, ev["cand"]
            elif ev["outcome"] == "regress":
                reports[tgt], scores[tgt] = inc_rep, ev["inc"]
            ev["harness_after"] = dict(H)
            self.log(ev)
            history.append({k: ev.get(k) for k in ("t", "builder", "target", "outcome", "inc", "cand", "reason")})
        exam = exam_instances(c)
        final = {}
        for slot in ("A", "B"):
            if slot == "B" and H["B"] == H["A"]:
                final["B"] = final["A"]
            else:
                final[slot] = self._slim(self._bm(H[slot], exam))
            self.log({"kind": "exam", "slot": slot, "harness": H[slot], "report": final[slot]})
        out = {"kind": "end", "run": self.run_id, "harness": H, "secret": self.secret,
               "usd": round(self.usd, 4), "model_errors": self.model_errors,
               "calls": self.calls, "wall_s": round(time.time() - t0, 1)}
        self.log(out)
        shutil.rmtree(self.dir / "scratch", ignore_errors=True)
        return out
