import subprocess
import time
import sys

with open('expected.txt', 'rb') as f:
    expected = f.read()

# Verify once and time multiple runs
times = []
for i in range(3):
    with open('input.txt', 'rb') as fin:
        t0 = time.perf_counter()
        p = subprocess.run([sys.executable, 'sortints.py'], stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        t1 = time.perf_counter()
    if p.returncode != 0 or p.stdout != expected:
        print(0)
        sys.exit(0)
    times.append(t1 - t0)

#Also verify edge cases on first run: empty input, leading/trailing spaces, 0, -00, huge numbers?
# Wait: does sort(key=int) preserve leading zeros if input has them, or are inputs standard integers?
# Wait: list(map(int, ...)) vs sort(key=int): if input is standard integers, they match, except if input has "+5" or "05".
# Let's check with standard integer formatting too:
edge_in = b"  10 -5  0 \n 100 -100 0 3 \n"
edge_exp = b"-100\n-5\n0\n0\n3\n10\n100\n"
p_edge = subprocess.run([sys.executable, 'sortints.py'], input=edge_in, stdout=subprocess.PIPE)
if p_edge.returncode != 0 or p_edge.stdout != edge_exp:
    print(0)
    sys.exit(0)

# Score: 1,000,000 ints / median time (ints per second, or 1000 / total_time)
best_t = min(times)
med_t = sorted(times)[1]
# Print operations per second (in thousands of ints/sec)
print(f"{1000.0 / med_t:.2f}")
