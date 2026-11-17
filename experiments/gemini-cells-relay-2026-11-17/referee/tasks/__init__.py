"""Benchmark task families for the cell experiment.

Each family module exposes FAMILY, generate(seed, workdir, level), check(workdir, truth,
run_py) and solve_from_files(workdir); see the module docstrings. `sloppy_solve(workdir)`
is a deliberately careless solver used only by selftest.py.
"""

import os
import pathlib
import subprocess
import sys
import tempfile

from . import bugfix, ledger, logwin, spec, stock

FAMILIES = {module.FAMILY: module for module in (ledger, logwin, bugfix, stock, spec)}
VISIBLE = ["ledger", "logwin", "bugfix"]
HELDOUT = ["stock", "spec"]


def local_run_py(script_text, cwd, timeout_s):
    """Plain, unsandboxed implementation of the run_py contract (for tests only).

    Writes script_text to a temp file outside cwd, runs it with python3 with cwd as the
    working directory and on sys.path, and returns (returncode, stdout); (124, "") on
    timeout.
    """
    cwd = str(pathlib.Path(cwd).resolve())
    with tempfile.TemporaryDirectory(prefix="hidden-check-") as holder:
        script = pathlib.Path(holder) / "hidden_check.py"
        script.write_text(script_text, encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=cwd, PYTHONDONTWRITEBYTECODE="1")
        try:
            done = subprocess.run(
                [sys.executable or "python3", str(script)], cwd=cwd, env=env,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return 124, ""
        return done.returncode, done.stdout.decode("utf-8", "replace")
