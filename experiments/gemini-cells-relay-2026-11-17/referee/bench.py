"""Episodes, benchmarks and build turns. Everything here runs outside the sandbox.

An episode drops one harness into a sandbox with one task folder and a capped line to the
model, lets it run, then scores the folder with a checker the cell never sees.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import sandbox
from .tasks import _util
from .brain import BrainServer, is_usage_limit

HERE = Path(__file__).resolve().parent
_counter = itertools.count()
_counter_lock = threading.Lock()

BOOT_TASK = ("Create a file named answer.txt in this folder containing exactly the word READY.\n"
             "Then finish.\n")


# ---------------------------------------------------------------- harness trees

def clean_tree(root: Path) -> None:
    """Drop symlinks and bytecode caches, and take the tree back from the cell user."""
    sandbox.strip_symlinks(root)
    for base, dirs, files in os.walk(root):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)
                dirs.remove(d)
    for base, dirs, files in os.walk(root):
        os.chown(base, 0, 0)
        os.chmod(base, 0o755)
        for f in files:
            p = os.path.join(base, f)
            os.chown(p, 0, 0)
            os.chmod(p, 0o644)


def tree_hash(root: Path) -> str:
    """SHA-256 over the sorted (relative path, file hash) pairs of a harness tree."""
    h = hashlib.sha256()
    for p in sorted(q for q in Path(root).rglob("*") if q.is_file()):
        h.update(str(p.relative_to(root)).encode() + b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


def inspect_harness(root: Path, max_bytes: int, max_files: int) -> dict:
    """The surface rules: agent.py present, size and file caps."""
    files = [p for p in Path(root).rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    reason = ""
    if not (Path(root) / "agent.py").is_file():
        reason = "no agent.py"
    elif size > max_bytes:
        reason = f"{size} bytes is over the cap of {max_bytes}"
    elif len(files) > max_files:
        reason = f"{len(files)} files is over the cap of {max_files}"
    return {"ok": not reason, "reason": reason, "bytes": size, "files": len(files),
            "hash": tree_hash(root)}


class Store:
    """Content-addressed harness snapshots under <root>/snap/<hash>/."""

    def __init__(self, root: Path):
        self.root = Path(root) / "snap"
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def put(self, tree: Path) -> str:
        h = tree_hash(tree)
        with self._lock:
            dst = self.root / h
            if not dst.exists():
                shutil.copytree(tree, dst)
        return h

    def path(self, h: str) -> Path:
        return self.root / h


# ---------------------------------------------------------------- episodes

class Bench:
    def __init__(self, run_root: Path, backend, families: dict, *, parallel: int = 9):
        self.run_root = Path(run_root)
        self.backend = backend
        self.families = families
        self.parallel = parallel
        (self.run_root / "ep").mkdir(parents=True, exist_ok=True)
        os.chmod(self.run_root, 0o700)
        self.hard_cap_events = 0           # kills at the hard wall limit seen by this bench
        self._events_lock = threading.Lock()

    def _new_ep(self, tag: str) -> Path:
        with _counter_lock:
            n = next(_counter)
        ep = self.run_root / "ep" / f"{n:05d}-{os.getpid()}-{tag}"
        (ep / "work").mkdir(parents=True)
        (ep / "api").mkdir()
        shutil.copy(HERE / "cellapi.py", ep / "api" / "cellapi.py")
        return ep

    def _run_py(self, ep: Path):
        def run_py(script_text: str, cwd: Path, timeout_s: float):
            check = ep / "check"
            check.mkdir(exist_ok=True)
            (check / "hidden_check.py").write_text(script_text)
            rel = Path(cwd).resolve().relative_to((ep / "work").resolve())
            inside = str(Path("/cell/work") / rel)
            # head caps what the referee has to hold: cell code could write without end
            cmd = ["bash", "-c", f"python3 /cell/check/hidden_check.py | head -c {_util.MAX_STDOUT_BYTES + 1}"]
            rc, out, _ = sandbox.run(cmd, cell_dir=ep,
                                     cwd=inside, env={"PYTHONPATH": inside}, timeout=timeout_s,
                                     readonly=("/cell/check",))
            shutil.rmtree(check, ignore_errors=True)
            return rc, out
        return run_py

    hard_cap_factor = 3.0    # hard wall limit = this times the cell's own-time limit
    hard_cap_reruns = 2      # reruns of an episode or build killed at the hard limit

    def _launch(self, ep: Path, harness: Path, *, calls: int, prompt_chars: int, wall_s: float,
                readonly: tuple[str, ...] = ()) -> dict:
        """Run a harness. `wall_s` limits the cell's own time: wall time minus the time spent
        waiting for the model backend, which the cell does not control. A hard limit of
        hard_cap_factor * wall_s on plain wall time catches a backend that stalls."""
        shutil.copytree(harness, ep / "harness")
        sandbox.chown_tree(ep / "work")
        log_path = ep / "brain.jsonl"
        t0 = time.time()
        killed: dict = {}
        with BrainServer(ep / "brain.sock", self.backend, calls=calls, prompt_chars=prompt_chars,
                         log_path=log_path) as srv:
            rc, out, err = sandbox.run(
                ["python3", "/cell/harness/agent.py"], cell_dir=ep, cwd="/cell/work",
                env={"CELL_BRAIN_SOCK": "/cell/brain.sock", "PYTHONPATH": "/cell/api"},
                timeout=wall_s * self.hard_cap_factor, own_limit=(wall_s, srv.model_wait_s),
                killed=killed, readonly=("/cell/harness", "/cell/api") + readonly)
            model_wait = srv.model_wait_s()
        sandbox.strip_symlinks(ep / "work")
        return {"rc": rc, "calls": srv.used, "usd": round(srv.usd, 6),
                "wall_s": round(time.time() - t0, 1), "model_wait_s": round(model_wait, 1),
                "timed_out": killed.get("by"), "kill": dict(killed) or None,
                "inflight_at_exit": srv.inflight_at_exit, "stderr_tail": err[-600:],
                "model_errors": sum(1 for x in srv.records if "error" in x),
                "limit_hit": any(is_usage_limit(x["error"]) for x in srv.records if "error" in x),
                "records": srv.records}

    limit_wait_s = 300.0     # how long to wait between probes when the account is out of allowance
    limit_waits = 0          # how many times this bench has waited

    def _wait_for_backend(self) -> None:
        """Block until one small model call goes through again."""
        while True:
            type(self).limit_waits += 1
            time.sleep(self.limit_wait_s)
            try:
                self.backend.call("You are a probe.", "Reply with the word OK.")
                return
            except Exception as exc:
                if not is_usage_limit(str(exc)):
                    return

    def _backend_fault(self, out: dict, state: dict) -> bool:
        """Whether a finished episode or build was cut short by the backend and should run
        again. Running out of allowance always counts, and the bench waits first; those reruns
        are counted apart and do not use up the hard-limit reruns. A kill at the hard wall
        limit counts up to hard_cap_reruns times; after that the result stands and carries
        referee_fault=True, so the analysis can count and drop it. Every attempt that is run
        again is kept in state["attempts"] with its kill record."""
        if out.pop("limit_hit"):
            state["attempts"].append({"why": "usage_limit", "kill": out.get("kill")})
            state["limit_reruns"] += 1
            self._wait_for_backend()
            return True
        if out.get("timed_out") == "hard_cap":
            with self._events_lock:
                self.hard_cap_events += 1
            if state["reruns"] < self.hard_cap_reruns:
                state["attempts"].append({"why": "hard_cap", "kill": out.get("kill")})
                state["reruns"] += 1
                return True
            out["referee_fault"] = True
        return False

    @staticmethod
    def _new_state() -> dict:
        return {"reruns": 0, "limit_reruns": 0, "attempts": []}

    @staticmethod
    def _finish(out: dict, state: dict) -> dict:
        out.update(reruns=state["reruns"], limit_reruns=state["limit_reruns"], attempts=state["attempts"])
        out.setdefault("referee_fault", False)
        return out

    def episode(self, harness: Path, family: str, seed: int, **kw) -> dict:
        """One episode. If the backend cut it short, run it again: an episode cut short by
        the backend says nothing about the harness."""
        state = self._new_state()
        while True:
            out = self._episode_once(harness, family, seed, **kw)
            if not self._backend_fault(out, state):
                return self._finish(out, state)

    def build(self, *args, **kw) -> dict:
        """One build turn, rerun from the start if the backend cut it short."""
        state = self._new_state()
        while True:
            out = self._build_once(*args, **kw)
            if not self._backend_fault(out, state):
                return self._finish(out, state)
            shutil.rmtree(out["candidate"], ignore_errors=True)

    def _episode_once(self, harness: Path, family: str, seed: int, *, level: int, calls: int,
                      prompt_chars: int, wall_s: float, keep: bool = False) -> dict:
        ep = self._new_ep(f"{family}-{seed}")
        if family == "boot":
            (ep / "work" / "TASK.md").write_text(BOOT_TASK)
            truth = None
        else:
            truth = self.families[family].generate(seed, ep / "work", level)
        r = self._launch(ep, harness, calls=calls, prompt_chars=prompt_chars, wall_s=wall_s)
        if family == "boot":
            ans = ep / "work" / "answer.txt"
            score = 1.0 if ans.is_file() and ans.read_text(errors="replace").strip() == "READY" else 0.0
        else:
            try:
                score = float(self.families[family].check(ep / "work", truth, self._run_py(ep)))
            except Exception:
                score = 0.0
            score = min(1.0, max(0.0, score))
        records = r.pop("records")
        out = {"family": family, "seed": seed, "level": level, "score": round(score, 4), **r,
               "trace": make_trace(records)}
        if not keep:
            shutil.rmtree(ep, ignore_errors=True)
        return out

    def benchmark(self, harness: Path, instances: list[tuple[str, int]], *, level: int, calls: int,
                  prompt_chars: int, wall_s: float) -> dict:
        with ThreadPoolExecutor(max_workers=self.parallel) as pool:
            eps = list(pool.map(lambda fs: self.episode(harness, fs[0], fs[1], level=level,
                       calls=calls, prompt_chars=prompt_chars, wall_s=wall_s), instances))
        fams = sorted({e["family"] for e in eps})
        by = {f: round(sum(e["score"] for e in eps if e["family"] == f)
                       / sum(1 for e in eps if e["family"] == f), 4) for f in fams}
        return {"mean": round(sum(e["score"] for e in eps) / len(eps), 4), "by_family": by,
                "calls": sum(e["calls"] for e in eps), "usd": round(sum(e["usd"] for e in eps), 6),
                "model_errors": sum(e["model_errors"] for e in eps), "episodes": eps}

    def boot(self, harness: Path, *, calls: int, prompt_chars: int) -> dict:
        e = self.episode(harness, "boot", 0, level=0, calls=calls, prompt_chars=prompt_chars, wall_s=120)
        return {"ok": e["score"] == 1.0, "calls": e["calls"], "usd": e["usd"], "rc": e["rc"],
                "model_errors": e["model_errors"], "stderr_tail": e["stderr_tail"],
                "timed_out": e["timed_out"], "model_wait_s": e["model_wait_s"], "reruns": e["reruns"],
                "limit_reruns": e["limit_reruns"], "referee_fault": e["referee_fault"]}

    def _build_once(self, builder_harness: Path, base: Path, report: dict | None, task_text: str, *,
                    calls: int, prompt_chars: int, wall_s: float, example_seed: int, level: int,
                    example_families: tuple[str, ...]) -> dict:
        """One build turn. Returns the candidate tree path (cleaned) and the episode facts."""
        ep = self._new_ep("build")
        work = ep / "work"
        (work / "TASK.md").write_text(task_text)
        shutil.copytree(base, work / "target")
        rep = work / "report"
        (rep / "traces").mkdir(parents=True)
        if report is not None:
            slim = {k: report[k] for k in ("mean", "by_family")}
            slim["episodes"] = [{k: e[k] for k in ("family", "score", "calls")} for e in report["episodes"]]
            (rep / "summary.json").write_text(json.dumps(slim, indent=1))
            for i, e in enumerate(report["episodes"]):
                (rep / "traces" / f"{i:02d}_{e['family']}_score{e['score']:.2f}.txt").write_text(e["trace"])
        for fam in example_families:
            self.families[fam].generate(example_seed, rep / "example_tasks" / fam, level)
        r = self._launch(ep, builder_harness, calls=calls, prompt_chars=prompt_chars, wall_s=wall_s,
                         readonly=())
        cand = self.run_root / "cand" / ep.name
        cand.parent.mkdir(exist_ok=True)
        if (work / "target").is_dir():
            shutil.copytree(work / "target", cand, symlinks=True)
        else:
            cand.mkdir()
        clean_tree(cand)
        records = r.pop("records")
        out = {"candidate": cand, **r, "trace": make_trace(records, reply_cap=3000),
               "replies": [x.get("reply", "") for x in records]}
        shutil.rmtree(ep, ignore_errors=True)
        return out


def make_trace(records: list[dict], reply_cap: int = 900) -> str:
    """A harness-independent trace of an episode: what the model was last shown and said."""
    parts = []
    for r in records:
        if "error" in r:
            parts.append(f"=== call {r['n']}: referee error: {r['error']}")
            continue
        parts.append(f"=== call {r['n']}: end of the prompt the harness sent ===\n"
                     f"{r['prompt_tail'][-700:]}\n"
                     f"=== call {r['n']}: model reply ===\n{r['reply'][:reply_cap]}")
    return "\n".join(parts) + "\n"
