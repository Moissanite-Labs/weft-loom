import subprocess, time, sys

with open('test_in.txt', 'rb') as f:
    in_data = f.read()
with open('test_ref.txt', 'rb') as f:
    ref_data = f.read()

# Run 3 iterations to get ~0.3-1.5s workload and take median time
times = []
for i in range(3):
    t0 = time.perf_counter()
    p = subprocess.run([sys.executable, 'sortints.py'], input=in_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.perf_counter()
    if p.returncode != 0 or p.stdout != ref_data:
        print(0)
        sys.exit(0)
    times.append(t1 - t0)

times.sort()
# Score: millions of ints per second (higher is better)
score = 1.0 / times[1]
print(f"{score:.4f}")
