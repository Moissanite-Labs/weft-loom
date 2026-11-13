import subprocess, sys, time
T = [5000000, 100000000, 100000000, 100000000, 30000000]
names = sys.argv[1:]
best = {x: 1e9 for x in names}
for _ in range(3):
    for x in names:
        t0 = time.perf_counter()
        for n in T:
            subprocess.run([sys.executable, x + ".py", str(n)], capture_output=True)
        best[x] = min(best[x], time.perf_counter() - t0)
for x in names:
    print(x, round(best[x], 4), "score~", round(100 / best[x], 1))
