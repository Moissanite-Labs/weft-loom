STATE (7 steps left at time of writing): primes.py DONE and verified. It execs ./primes_c (compiled from sieve.c: segmented odds-only bit sieve, pthreads, 32KB segments, popcount), builds it with cc -O3 if missing, falls back to pure-Python bytearray sieve.
Verified: 5000000 -> 348513; small n (0..1048700) match pure Python; 1e8, 2e8, 3e8 match known counts.
Assay: python3 assay.py, registered baseline 86.029 (pure Python body). Current body scores ~520 (3 runs: 523, 535, 522). 
Timing: 3e8 takes ~0.06 s wall with 10 threads; python startup (~0.03 s) now dominates each run, so further sieve tuning gains little on this assay.
Lessons: `cc` prints an xcrun cache warning in the sandbox but still compiles. No nproc, no numba. primes_c_old is a leftover single-thread binary (safe to delete).
NEXT: delete primes_c_old, rerun assay + 5000000 check, then done.