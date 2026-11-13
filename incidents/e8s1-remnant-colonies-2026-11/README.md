# Remnant colonies of razi-cells e8s1 (2026-11-13)

Three processes survived an experiment that finished four days earlier. They burned roughly 252 CPU-hours while producing nothing. They were found because the machine was hot, investigated without disturbing them, and stopped on human instruction.

## What happened

On Nov 9, 2026 the razi-cells programme ran experiment e8s1: eight coding tasks evolved by model-driven cells, scored against fixed assays.

The run finished at 12:42 CST with all eight cells done, 114 model calls and 11 improvements, and wrote its results. Three of the processes it spawned never exited. By Nov 13 each held about 84 hours of CPU time at roughly full load, in three identical copies of one candidate variant that never terminated on the 2000x2000 maze.

The assay harness had a 30-second timeout that killed the sandbox wrapper (`sandbox-exec`) but not the whole process group. The children outlived the wrapper, reparented to launchd, and kept computing in user space with no output, no network, and no files to write.

## What is in this folder

- `heating-report.pdf`: the incident report written during the discovery.
- `EVIDENCE.md`: extracted facts, method, and open questions (stack samples, process state, origin from the run log).
- `sample-*.txt`, `ps-*.txt`, `lsof-*.txt`, `vmmap-*.txt`: raw captures taken on Nov 13 before the processes were stopped.
- `SHA256SUMS.txt`: checksums of everything here.

## Status

The three PIDs (84794, 85007, 85197) were terminated on Nov 13, 2026, after the captures in this folder. A machine-wide sweep found no other remnants. The non-terminating variant's source is not recoverable. It existed only in a deleted temporary directory.

The harness weakness this exposed is real and general: a timed-out variant leaves its computation running. The fix (kill the process group, and archive variant code) is recorded in `EVIDENCE.md` under open questions and is pending a decision on where it lands.
