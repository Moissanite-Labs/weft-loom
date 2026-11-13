import os, sys, ctypes, subprocess

so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.so")
c_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.c")

if not os.path.exists(so_path) and os.path.exists(c_path):
    cur = os.path.dirname(os.path.abspath(__file__))
    env = dict(os.environ, TMPDIR=cur, TMP=cur, TEMP=cur)
    o_path = os.path.join(cur, "_csvsum.o")
    subprocess.run(["clang", "-O3", "-fPIC", "-c", c_path, "-o", o_path], env=env, check=False)
    subprocess.run(["clang", "-O3", "-dynamiclib", o_path, "-o", so_path, "-lpthread"], env=env, check=False)

if os.path.exists(so_path):
    lib = ctypes.CDLL(so_path)
    lib.run_csvsum()
else:
    from collections import defaultdict
    sums = defaultdict(float)
    lines = sys.stdin.buffer
    next(lines, None)
    for line in lines:
        _, cat, val = line.split(b',')
        sums[cat] += float(val)
    for cat in sorted(sums):
        print(f"{cat.decode()},{sums[cat]:.2f}")
