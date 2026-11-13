primes.py status: DONE-ready. Segmented odd-only sieve, 1MB segments copied from a pre-sieved pattern (3,5,7,11,13; period 15015), 8 forked workers returning counts over pipes; simple sieve for n < 65536.
Verified: 5000000 -> 348513, 100000000 -> 5761455, chk.py (30 n values incl. boundaries + random vs reference sieve) bad 0.
Assay (python3 assay.py, runs/sec on n=1e8): 5.52 original baseline -> ~16-18 now. Run is ~55 ms, of which ~33 ms is bare interpreter startup.
Tried, no gain: 10 workers, 512KB or 8MB segments, pre-sieve through 17. Remaining headroom is small; do not hardcode answers.