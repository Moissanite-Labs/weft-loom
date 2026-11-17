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
from .brain import BrainServer

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
            rc, out, _ = sandbox.run(["python3", "/cell/check/hidden_check.py"], cell_dir=ep,
                                     cwd=inside, env={"PYTHONPATH": inside}, timeout=timeout_s,
                                     readonly=("/cell/check",))
            shutil.rmtree(check, ignore_errors=True)
            return rc, out
        return run_py

    def _launch(self, ep: Path, harness: Path, *, calls: int, prompt_chars: int, wall_s: float,
                readonly: tuple[str, ...] = ()) -> dict:
        shutil.copytree(harness, ep / "harness")
        sandbox.chown_tree(ep / "work")
        log_path = ep / "brain.jsonl"
        t0 = time.time()
        with BrainServer(ep / "brain.sock", self.backend, calls=calls, prompt_chars=prompt_chars,
                         log_path=log_path) as srv:
            rc, out, err = sandbox.run(
                ["python3", "/cell/harness/agent.py"], cell_dir=ep, cwd="/cell/work",
                env={"CELL_BRAIN_SOCK": "/cell/brain.sock", "PYTHONPATH": "/cell/api"},
                timeout=wall_s, readonly=("/cell/harness", "/cell/api") + readonly)
        sandbox.strip_symlinks(ep / "work")
        return {"rc": rc, "calls": srv.used, "usd": round(srv.usd, 6),
                "wall_s": round(time.time() - t0, 1), "stderr_tail": err[-600:],
                "records": srv.records}

    def episode(self, harness: Path, family: str, seed: int, *, level: int, calls: int,
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
                "episodes": eps}

    def boot(self, harness: Path, *, calls: int, prompt_chars: int) -> dict:
        e = self.episode(harness, "boot", 0, level=0, calls=calls, prompt_chars=prompt_chars, wall_s=120)
        return {"ok": e["score"] == 1.0, "calls": e["calls"], "usd": e["usd"], "rc": e["rc"],
                "stderr_tail": e["stderr_tail"]}

    def build(self, builder_harness: Path, base: Path, report: dict | None, task_text: str, *,
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
