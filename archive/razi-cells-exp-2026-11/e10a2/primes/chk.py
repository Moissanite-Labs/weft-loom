import subprocess, sys, random
def ref(n):
    if n < 3: return 0
    s = bytearray([1]) * n
    s[0] = s[1] = 0
    i = 2
    while i * i < n:
        if s[i]:
            s[i*i::i] = bytes(len(range(i*i, n, i)))
        i += 1
    return s.count(1)
random.seed(7)
ns = [6, 7, 8, 9, 49, 50, 65535, 65536, 65537, 4194303, 4194304, 4194305, 4194306, 5000000, 16777216, 16777217, 9999991, 9999992]
ns += [random.randrange(65536, 20000000) for _ in range(12)]
bad = 0
for n in ns:
    got = subprocess.run([sys.executable, "primes.py", str(n)], capture_output=True, text=True).stdout.strip()
    if got != str(ref(n)):
        bad += 1
        print("MISMATCH", n, got, ref(n))
print("checked", len(ns), "bad", bad)
