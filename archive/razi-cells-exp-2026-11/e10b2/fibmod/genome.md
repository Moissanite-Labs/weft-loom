fibmod.py DONE and verified (check.py ok, fib(10)=55, fib(1e18)=209783453).
Design: Pisano period of 1e9+7 divides 2000000016, so n %= 2000000016 first.
- CLI path (__main__): fast doubling, no tables. ~25 ms per run, all Python startup; algorithm choice makes no measurable CLI difference.
- Import path fib(n): 3 precomputed tables (11+10+10 bits) of (F(k),F(k+1)) combined with addition formula. ~2.1M calls/s vs 180k for fast doubling (assay baseline 179670, noise 11%).
Assay = python3 assay.py: checks CLI on 8 inputs vs independent matrix power, 1500 random in-process checks, then throughput of imported fib (NOT CLI time).
Lesson: CLI time is interpreter startup; only in-process throughput is improvable. Building tables at CLI time costs ~1 ms, so keep them out of __main__.
Next: nothing needed; call done.