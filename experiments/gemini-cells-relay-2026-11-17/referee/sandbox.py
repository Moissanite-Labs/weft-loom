"""Run untrusted cell code with no network, no credentials and one writable folder.

A cell process sees the host system files read-only and nothing of /home, /root, /tmp,
/srv, /mnt or /media. Its episode folder is bound at /cell. It runs as uid 65534 in new
mount, network and pid namespaces, with an empty environment apart from the variables
passed in. `tests/sandbox_selftest.py` checks each of these properties from the inside.

Linux only. The caller must be root (the referee runs as root in a throwaway container).
"""

from __future__ import annotations

import os
import shlex
import signal
import subprocess
import time
from pathlib import Path

CELL_UID = 65534
CELL_GID = 65534
MOUNTPOINT = "/cell"
MASKED = ("/home", "/root", "/tmp", "/srv", "/mnt", "/media", "/var/tmp", "/run")
PATH = "/usr/local/bin:/usr/bin:/bin"

_INNER = r"""
set -e
mount --make-rprivate /
mount --bind "$1" /cell
shift
while [ "$1" != "--" ]; do
  mount --bind "$1" "$1"
  mount -o remount,ro,bind "$1"
  shift
done
shift
for d in __MASKED__; do
  [ -d "$d" ] && mount -t tmpfs -o size=16m,mode=755 tmpfs "$d"
done
chmod 1777 /tmp
cd "$1"
shift
exec setpriv --reuid=__UID__ --regid=__GID__ --clear-groups --no-new-privs \
  prlimit --as=3221225472 --fsize=67108864 --nproc=512 --core=0 -- "$@"
"""


def chown_tree(root: Path) -> None:
    """Give a folder to the cell user. Symlinks are not followed."""
    for base, dirs, files in os.walk(root):
        os.lchown(base, CELL_UID, CELL_GID)
        for name in dirs + files:
            os.lchown(os.path.join(base, name), CELL_UID, CELL_GID)


def strip_symlinks(root: Path) -> int:
    """Delete every symlink under root, so the referee never reads through one."""
    removed = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs) + files:
            p = os.path.join(base, name)
            if os.path.islink(p):
                os.unlink(p)
                removed += 1
                if name in dirs:
                    dirs.remove(name)
    return removed


def run(
    cmd: list[str],
    *,
    cell_dir: Path,
    cwd: str = "/cell",
    env: dict[str, str] | None = None,
    timeout: float = 60.0,
    readonly: tuple[str, ...] = (),
    own_limit: tuple[float, "callable"] | None = None,
    killed: dict | None = None,
) -> tuple[int, str, str]:
    """Run cmd in the sandbox. cell_dir is bound at /cell. Paths in `readonly` are given
    as they appear inside the sandbox (under /cell) and are remounted read-only.
    Returns (returncode, stdout, stderr); 124 on timeout.

    `timeout` is a hard limit on wall time. With own_limit = (seconds, wait_fn) the process
    is also killed once its wall time minus wait_fn() passes `seconds`: wait_fn reports the
    time spent waiting on something the cell does not control (the model backend), which is
    not charged to the cell. If `killed` is a dict, it receives "by": "own_time" or
    "hard_cap" when the process is killed, plus the two clocks at that moment."""
    if os.geteuid() != 0:
        raise RuntimeError("the sandbox launcher needs root")
    os.makedirs(MOUNTPOINT, exist_ok=True)
    inner = (
        _INNER.replace("__MASKED__", " ".join(MASKED))
        .replace("__UID__", str(CELL_UID))
        .replace("__GID__", str(CELL_GID))
    )
    full_env = {"PATH": PATH, "HOME": "/cell", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    full_env.update(env or {})
    argv = [
        "unshare", "--mount", "--net", "--pid", "--fork", "--kill-child", "--mount-proc",
        "bash", "-c", inner, "sandbox", str(cell_dir), *readonly, "--", cwd, *cmd,
    ]
    proc = subprocess.Popen(
        argv, env=full_env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True,
    )
    started = time.monotonic()
    while True:
        elapsed = time.monotonic() - started
        waited = own_limit[1]() if own_limit else 0.0
        if elapsed >= timeout:
            reason = "hard_cap"
        elif own_limit and elapsed - waited >= own_limit[0]:
            reason = "own_time"
        else:
            reason = None
        if reason:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            out, err = proc.communicate()
            if killed is not None:
                killed.update({"by": reason, "wall_s": round(elapsed, 1), "wait_s": round(waited, 1)})
            rc = 124
            break
        step = min(0.5, max(0.01, timeout - elapsed))
        if own_limit:
            step = min(step, max(0.01, own_limit[0] - (elapsed - waited)))
        try:
            out, err = proc.communicate(timeout=step)
            rc = proc.returncode
            break
        except subprocess.TimeoutExpired:
            continue
    return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def describe() -> str:
    return "unshare(mount,net,pid) + tmpfs over " + ",".join(MASKED) + f" + setpriv uid {CELL_UID}"


if __name__ == "__main__":
    import sys
    rc, out, err = run(sys.argv[2:], cell_dir=Path(sys.argv[1]))
    sys.stdout.write(out)
    sys.stderr.write(err)
    print("rc", rc, "|", shlex.join(sys.argv[2:]))
