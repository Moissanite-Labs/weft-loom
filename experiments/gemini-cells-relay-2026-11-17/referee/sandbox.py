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
) -> tuple[int, str, str]:
    """Run cmd in the sandbox. cell_dir is bound at /cell. Paths in `readonly` are given
    as they appear inside the sandbox (under /cell) and are remounted read-only.
    Returns (returncode, stdout, stderr); 124 on timeout."""
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
    try:
        out, err = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = proc.communicate()
        rc = 124
    return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def describe() -> str:
    return "unshare(mount,net,pid) + tmpfs over " + ",".join(MASKED) + f" + setpriv uid {CELL_UID}"


if __name__ == "__main__":
    import sys
    rc, out, err = run(sys.argv[2:], cell_dir=Path(sys.argv[1]))
    sys.stdout.write(out)
    sys.stderr.write(err)
    print("rc", rc, "|", shlex.join(sys.argv[2:]))
