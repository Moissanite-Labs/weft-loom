"""Model access for cells, kept on the referee's side of the sandbox.

`BrainServer` listens on a Unix socket inside one episode folder. It enforces the
episode's call cap and prompt cap, logs every exchange, and forwards the call to a
backend. `ClaudeCLI` is the live backend (one headless `claude -p` process per call, tools
off). `Scripted` is the offline backend used by the tests.

Spend is tracked in one ledger file per run root, with a hard cap: when the cap is
reached every further live call fails, in every process that shares the ledger.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path

_CLI_SLOTS = threading.BoundedSemaphore(int(os.environ.get("GC_CLI_PARALLEL", "10")))


class SpendCapReached(RuntimeError):
    pass


class Ledger:
    """A JSON file {"usd": x, "calls": n} updated under a file lock."""

    def __init__(self, path: Path, cap_usd: float):
        self.path = Path(path)
        self.cap = float(cap_usd)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"usd": 0.0, "calls": 0}))

    def _locked(self, fn):
        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            data = json.loads(f.read() or "{}")
            out = fn(data)
            f.seek(0)
            f.truncate()
            f.write(json.dumps(data))
            return out

    def check(self) -> None:
        if self._locked(lambda d: d.get("usd", 0.0)) >= self.cap:
            raise SpendCapReached(f"spend cap of {self.cap} dollars reached")

    def add(self, usd: float) -> None:
        def upd(d):
            d["usd"] = d.get("usd", 0.0) + usd
            d["calls"] = d.get("calls", 0) + 1
        self._locked(upd)

    def read(self) -> dict:
        return self._locked(lambda d: dict(d))


class Scripted:
    """Offline backend: reply = fn(system, prompt). Costs nothing."""

    name = "scripted"

    def __init__(self, fn):
        self.fn = fn

    def call(self, system: str, prompt: str) -> dict:
        return {"reply": self.fn(system, prompt), "usd": 0.0, "in_tok": 0, "out_tok": 0, "api_ms": 0}


class ClaudeCLI:
    """Live backend. One `claude -p` process per call: no tools, no session, no thinking."""

    def __init__(self, model: str, ledger: Ledger, timeout: float = 180.0):
        self.model = model
        self.name = model
        self.ledger = ledger
        self.timeout = timeout
        self._cwd = tempfile.mkdtemp(prefix="gc-brain-")

    def call(self, system: str, prompt: str) -> dict:
        self.ledger.check()
        env = dict(os.environ)
        env["MAX_THINKING_TOKENS"] = "0"
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "6000"
        argv = ["claude", "-p", "--model", self.model, "--tools", "", "--output-format", "json",
                "--no-session-persistence", "--system-prompt", system]
        last = "no attempt"
        for attempt in range(3):
            with _CLI_SLOTS:
                try:
                    p = subprocess.run(argv, input=prompt.encode("utf-8"), capture_output=True,
                                       timeout=self.timeout, cwd=self._cwd, env=env)
                    d = json.loads(p.stdout.decode("utf-8", "replace"))
                except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                    last = f"{type(exc).__name__}"
                    time.sleep(2 + 4 * attempt)
                    continue
            usd = float(d.get("total_cost_usd") or 0.0)
            if usd:
                self.ledger.add(usd)
            if d.get("is_error") or not isinstance(d.get("result"), str):
                last = str(d.get("result") or d.get("subtype") or "error")[:200]
                time.sleep(2 + 4 * attempt)
                continue
            u = d.get("usage") or {}
            in_tok = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                      + u.get("cache_read_input_tokens", 0))
            return {"reply": d["result"], "usd": usd, "in_tok": in_tok,
                    "out_tok": u.get("output_tokens", 0), "api_ms": d.get("duration_api_ms", 0)}
        raise RuntimeError(f"model call failed three times: {last}")


def clip_middle(text: str, cap: int) -> tuple[str, bool]:
    """Keep the head and the tail of an over-long prompt. Returns (text, was_clipped)."""
    if len(text) <= cap:
        return text, False
    head = int(cap * 0.4)
    tail = cap - head - 40
    return text[:head] + "\n[... clipped by the referee ...]\n" + text[-tail:], True


class BrainServer:
    """Serves one episode. Use as a context manager."""

    def __init__(self, sock_path: Path, backend, *, calls: int, prompt_chars: int, log_path: Path):
        self.sock_path = Path(sock_path)
        self.backend = backend
        self.calls = calls
        self.prompt_chars = prompt_chars
        self.log_path = Path(log_path)
        self.used = 0
        self.usd = 0.0
        self.records: list[dict] = []
        self._lock = threading.Lock()
        self._stop = False
        self._srv = None
        self._thread = None

    def __enter__(self):
        if self.sock_path.exists():
            self.sock_path.unlink()
        self._srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._srv.bind(str(self.sock_path))
        os.chmod(self.sock_path, 0o666)
        self._srv.listen(8)
        self._srv.settimeout(0.5)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop = True
        self._thread.join(timeout=5)
        self._srv.close()
        try:
            self.sock_path.unlink()
        except FileNotFoundError:
            pass
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w") as f:
            for r in self.records:
                f.write(json.dumps(r) + "\n")

    def _loop(self):
        while not self._stop:
            try:
                conn, _ = self._srv.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn):
        try:
            conn.settimeout(600)
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = conn.recv(1 << 16)
                if not chunk:
                    break
                buf += chunk
                if len(buf) > 4_000_000:
                    break
            try:
                req = json.loads(buf.decode("utf-8", "replace"))
            except json.JSONDecodeError:
                req = {}
            conn.sendall((json.dumps(self._handle(req)) + "\n").encode("utf-8"))
        except OSError:
            pass
        finally:
            conn.close()

    def _handle(self, req: dict) -> dict:
        op = req.get("op")
        if op == "left":
            return {"left": max(0, self.calls - self.used), "calls": self.calls,
                    "prompt_chars": self.prompt_chars}
        if op != "call":
            return {"error": "unknown op"}
        with self._lock:
            if self.used >= self.calls:
                return {"error": "budget"}
            self.used += 1
            n = self.used
        system = str(req.get("system", ""))[:8000]
        prompt, clipped = clip_middle(str(req.get("prompt", "")), self.prompt_chars)
        t0 = time.time()
        try:
            r = self.backend.call(system, prompt)
        except Exception as exc:  # the cell sees a plain error; the log keeps the cause
            self.records.append({"n": n, "error": f"{type(exc).__name__}: {exc}"[:300]})
            return {"error": "model call failed"}
        self.usd += r["usd"]
        self.records.append({
            "n": n, "system_sha": hashlib.sha256(system.encode()).hexdigest()[:16],
            "system_chars": len(system), "prompt_chars": len(prompt), "clipped": clipped,
            "prompt_head": prompt[:300], "prompt_tail": prompt[-1500:], "reply": r["reply"],
            "usd": r["usd"], "in_tok": r["in_tok"], "out_tok": r["out_tok"],
            "api_ms": r["api_ms"], "wall_s": round(time.time() - t0, 2),
        })
        return {"reply": r["reply"]}
