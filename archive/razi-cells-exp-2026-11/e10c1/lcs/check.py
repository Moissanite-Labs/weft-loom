import random, subprocess, sys, time, importlib

def ref(a, b):
    prev = [0]*(len(b)+1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b):
            cur.append(prev[j]+1 if ca == cb else max(prev[j+1], cur[j]))
        prev = cur
    return prev[-1]

def run(a, b):
    out = subprocess.run([sys.executable, "lcs.py"], input=(a+"\n"+b+"\n").encode(), capture_output=True)
    return int(out.stdout.decode().strip())

random.seed(1)
cases = [("", ""), ("abc", ""), ("", "abc"), ("abc", "abc"), ("abc", "def"), ("ACGT"*5, "GTCA"*5)]
for _ in range(30):
    n = random.randint(0, 60); m = random.randint(0, 60)
    cases.append(("".join(random.choice("ab") for _ in range(n)), "".join(random.choice("abc") for _ in range(m))))
for a, b in cases:
    if run(a, b) != ref(a, b):
        print("FAIL", a, b); sys.exit(1)

random.seed(7)
a = "".join(random.choice("ACGT") for _ in range(3000))
b = "".join(random.choice("ACGT") for _ in range(3000))
exp = 1948  # verified once with ref(a, b)
if run(a, b) != exp:
    print("FAIL big"); sys.exit(1)

# in-process timing: heavy workload, immune to process startup noise
lcs = importlib.import_module("lcs")
f = lcs.lcs_len
if f(a, b) != exp:
    print("FAIL big inproc"); sys.exit(1)
times = []
for _ in range(15):
    t = time.perf_counter()
    for _ in range(20):
        f(a, b)
    times.append(time.perf_counter() - t)
times.sort()
k = max(1, len(times)//3)
print(20 * k / sum(times[:k]))
