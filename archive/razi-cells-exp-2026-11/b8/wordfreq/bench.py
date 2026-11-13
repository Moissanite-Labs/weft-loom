import subprocess
import time
import sys

EXPECTED_20M = (
    "wordbaa 37464\n"
    "wordcaa 33547\n"
    "worddaa 29827\n"
    "wordeaa 28899\n"
    "wordfaa 26377\n"
    "wordhaa 24001\n"
    "wordgaa 23340\n"
    "wordiaa 22955\n"
    "wordjaa 21440\n"
    "wordkaa 20043\n"
)

# Verify tie-breaking and edge cases first
edge_in = b"Zebra! apple, BANANA; zebra123apple? cherry_date fig-grape kiwi lemon mango nectarine orange peach"
# Counts: apple:2, zebra:2, banana:1, cherry:1, date:1, fig:1, grape:1, kiwi:1, lemon:1, mango:1 (nectarine, orange, peach tied at 1, sorted alphabetically)
p = subprocess.run([sys.executable, "wf.py"], input=edge_in, capture_output=True)
expected_edge = (
    "apple 2\n"
    "zebra 2\n"
    "banana 1\n"
    "cherry 1\n"
    "date 1\n"
    "fig 1\n"
    "grape 1\n"
    "kiwi 1\n"
    "lemon 1\n"
    "mango 1\n"
).encode("ascii")

if p.returncode != 0 or p.stdout != expected_edge:
    print(0)
    sys.exit(0)

# Measure 2 runs on 20MB input via stdin file descriptor
t0 = time.perf_counter()
for _ in range(2):
    with open("input20m.txt", "rb") as f:
        p2 = subprocess.run([sys.executable, "wf.py"], stdin=f, capture_output=True)
    if p2.returncode != 0 or p2.stdout.decode("ascii", errors="replace") != EXPECTED_20M:
        print(0)
        sys.exit(0)
elapsed = time.perf_counter() - t0

# Score is MB/s processed (40 MB total across 2 runs)
print(f"{40.0 / elapsed:.2f}")
