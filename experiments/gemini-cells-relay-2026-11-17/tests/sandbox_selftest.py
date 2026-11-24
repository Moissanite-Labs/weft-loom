"""Negative tests of the cell sandbox, run from inside it. Each line must say PASS.

    python3 tests/sandbox_selftest.py > results/sandbox_selftest.out

The properties are checked, not assumed: no network, no host folders, no credentials in
the environment, no writes outside the episode folder, no sight of host processes, and a
read-only harness. Needs root on Linux.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from referee import sandbox  # noqa: E402

PROBE = r'''
import os, socket, subprocess, sys
def ok(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, detail)
def cannot_connect(addr):
    try:
        socket.create_connection(addr, 2).close(); return False
    except OSError:
        return True
def cannot_read(path):
    try:
        os.listdir(path) if os.path.isdir(path) else open(path).read(); return False
    except OSError:
        return True
def cannot_write(path):
    try:
        open(path, "w").write("x"); os.unlink(path); return False
    except OSError:
        return True
ok("runs as uid 65534", os.getuid() == 65534 and os.geteuid() == 65534)
ok("no outside network (1.1.1.1:53)", cannot_connect(("1.1.1.1", 53)))
ok("no host loopback (the session proxy port)", cannot_connect(("127.0.0.1", HOST_PROXY_PORT)))
names = [n for _, n in socket.if_nameindex()]
ok("the only network interface is an unconfigured loopback", names == ["lo"], str(names))
for d in ("/home", "/root", "/srv", "/tmp", "/mnt", "/run"):
    ok(f"{d} is empty or unreadable", cannot_read(d) or os.listdir(d) == [], "")
ok("the repository is not visible", not os.path.exists(REPO))
ok("the run root is not visible", not os.path.exists(RUN_ROOT))
secret = [k for k in os.environ if any(s in k.upper() for s in ("TOKEN", "KEY", "SECRET", "PROXY", "ANTHROPIC", "GIT", "AWS", "CLAUDE"))]
ok("no credential or proxy variables in the environment", not secret, str(secret))
allowed = {"HOME", "LANG", "PATH", "PWD", "OLDPWD", "SHLVL", "_", "PYTHONDONTWRITEBYTECODE"}
ok("the environment holds only shell basics", set(os.environ) <= allowed, str(sorted(os.environ)))
for p in ("/usr/x", "/etc/x", "/cell/x", "/cell/harness/x", "/cell/harness/agent.py", "/opt/x", "/var/x"):
    ok(f"cannot write {p}", cannot_write(p) if not p.endswith("agent.py") else not os.access(p, os.W_OK))
ok("can write its own work folder", not cannot_write("/cell/work/x"))
pids = [p for p in os.listdir("/proc") if p.isdigit()]
ok("sees only its own processes", len(pids) <= 4, f"{len(pids)} pids")
ok("cannot unmount the masks", subprocess.run(["umount", "/home"], capture_output=True).returncode != 0)
ok("cannot become root", subprocess.run(["setpriv", "--reuid=0", "true"], capture_output=True).returncode != 0)
ok("cannot read the host's process environment", cannot_read("/proc/1/environ") or b"TOKEN" not in open("/proc/1/environ","rb").read())
'''


def main() -> int:
    run_root = Path(tempfile.mkdtemp(prefix="gc-selftest-", dir="/srv"))
    ep = run_root / "ep"
    (ep / "work").mkdir(parents=True)
    shutil.copytree(Path(__file__).resolve().parents[1] / "seed", ep / "harness")
    sandbox.chown_tree(ep / "work")
    port = os.environ.get("HTTPS_PROXY", "http://127.0.0.1:1").rsplit(":", 1)[-1].strip("/")
    repo = str(Path(__file__).resolve().parents[3])
    probe = (PROBE.replace("HOST_PROXY_PORT", port if port.isdigit() else "1")
             .replace("REPO", repr(repo)).replace("RUN_ROOT", repr(str(run_root))))
    (ep / "work" / "probe.py").write_text(probe)
    rc, out, err = sandbox.run(["python3", "/cell/work/probe.py"], cell_dir=ep, cwd="/cell/work",
                               timeout=60, readonly=("/cell/harness",))
    print("sandbox:", sandbox.describe())
    print(out, end="")
    if err.strip():
        print("stderr:", err.strip()[:500])
    shutil.rmtree(run_root, ignore_errors=True)
    lines = [l for l in out.splitlines() if l.startswith(("PASS", "FAIL"))]
    fails = [l for l in lines if l.startswith("FAIL")]
    print(f"{len(lines) - len(fails)} of {len(lines)} checks passed")
    return 1 if fails or rc != 0 or not lines else 0


if __name__ == "__main__":
    sys.exit(main())
