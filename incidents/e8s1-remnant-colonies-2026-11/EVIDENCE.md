# Remnant colonies of razi-cells e8s1: captured evidence, 2026-11-13

Three `Python maze.py` processes survived the e8s1 run (Nov 9, 2026) as orphans of the maze cell's variant benchmark. They were found Nov 13, 2026 (PID 84794: 87 h elapsed, ~84 h user CPU) and sampled read-only on Nov 13, 2026 04:28-04:29 CST. They were terminated the same morning on human instruction.

## What they were

- PIDs 84794, 85007, 85197. PPID 1 (launchd), PGID 75681, single thread each.
- Command line: `Python maze.py` (Homebrew CPython 3.14.8).
- cwd: `/Users/kethuda/work/razi-cells/exp/e8s1/maze/.tmp/v-x60b5u2l/v2` (directory deleted by the harness after the assay completed; node 420550486).
- stdin/stdout/stderr: pipes whose other ends died with the sandbox wrapper at the 30 s assay timeout.
- ~5,020 h of user CPU each as of capture. ~92% average duty since launch. R state. Physical footprint ~7.2-7.5 MB each, flat.

## Origin (from the e8s1 record, files unchanged since Nov 9 12:42)

- Launcher: `exp/run_e08.sh` (`colony.py ... --par 8 --calls 40 --steps 16`, model `opencode-go:gemini-4-argon`).
- The maze cell's second `variants` call (log.jsonl, t=1794249658.89, 2026-11-09 12:40:58 CST): medians `inc=67.4058, v0=69.5889, v1=66.9166, v2=0.0, v3=56.6461`, winner `v0` adopted (+3%), arm `safebold`.
- `v2` was a bold candidate described in the log as a 0-1 detour bucket A*. Its score of 0.0 means `sandboxed()` returned "timeout" after `SH_TIMEOUT` (30 s) on every repeat.
- REPEATS defaults to 5 (`CELL_REPEATS` unset), so `v2` was benched up to five times. Three orphan copies persisted; the cwd path `.../v-x60b5u2l/v2` names the candidate directory.
- The 0.0 in the first `variants` call (t=1794249461.57, medians `v3=0.0`) is the same mechanism; its survivors (if any) were not found.

## Harness mechanism (from source, ~/Work/razi-tools/cells/cell.py)

`sandboxed()` runs `sandbox-exec` under `subprocess.run(..., timeout=SH_TIMEOUT)`. On timeout, Python kills only the direct child (`sandbox-exec`). The descendants `sh`, `python3 bench.py`, `python3 maze.py` are not in the kill path. They were re-parented to launchd, memory-flat, and kept executing the algorithm in user space.

## What the stack samples show

`sample <pid> 1` (1 ms resolution) on all three: exclusively CPython `_PyEval_EvalFrameDefault` with a divmod-heavy integer hot path (`l_divmod`, `long_divmod`), `bytearray_subscript`, and attribute lookups. Structurally identical across the three. No C-extensions, no native code below the interpreter. Consistent with a non-terminating pure-Python maze solver, not I/O, not kernel time.

## Contents of this folder

- `sample-PID.txt` - 1-second stack dumps, three PIDs (taken Nov 13, 2026 04:28 CST).
- `ps-snapshot.txt` / `ps-threads-snapshot.txt` - state, elapsed, CPU time, RSS, threads, at capture.
- `lsof-snapshot.txt` - open files and cwd at capture.
- `vmmap-PID.txt` - memory anatomy at capture.
- `uname-capture.txt`, `date-utc-capture.txt` - platform and capture time.

## Other evidence elsewhere

- `heating-report.pdf`: the Nov 13 incident report written by the amp-cayde agent, included with the owner's instruction.
- `exp/e8s1/maze/log.jsonl`: the two `variants` events quoted above; e8s1 files frozen since Nov 9 12:42 CST.
- `exp/e8s1/summary.json`: run closed with 8/8 done, 114 calls, 11 improvements, 923.7 s wall.
- `variants.jsonl` contains only the cell's own file writes. Per-variant archives are absent, so the non-terminating variant's source is not recoverable from the record.
- Machine-wide sweep (ps, lsof) on Nov 13 found no other orphaned variant processes.

## Open questions

1. Which specific loop or bug inside the `v2` candidate never terminates (needs interpreter memory, or a from-scratch reconstruction).
2. Why the two copies of the candidate from other repeats are absent (exited, crashed, or never survived).
3. Whether the programme's other dozens of 0.0-variant timeouts left short-lived orphans that are no longer observable.
4. What should supervise long-running cell jobs so a finished colony cannot leave workers behind (harness fix discussion pending human decision).
