import subprocess, sys, time, os

MB = os.path.getsize("big.txt") / 1e6
ref = open("out_ref.txt", "rb").read()

# correctness gate
with open("big.txt", "rb") as f:
    r = subprocess.run([sys.executable, "wf.py"], stdin=f,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
if r.returncode != 0 or r.stdout != ref:
    print(0)
    sys.exit(0)

best = 1e9
for _ in range(3):
    with open("big.txt", "rb") as f:
        t0 = time.perf_counter()
        subprocess.run([sys.executable, "wf.py"], stdin=f,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        best = min(best, time.perf_counter() - t0)

print(MB / best)   # throughput in MB/s, higher is better
