import subprocess, time, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
ref = open('ref.out', 'rb').read()
t = time.perf_counter()
r = subprocess.run([sys.executable, 'csvsum.py'], stdin=open('data.csv', 'rb'), capture_output=True)
dt = time.perf_counter() - t
ok = r.returncode == 0 and r.stdout == ref
print(1000.0 / dt if ok else 0)
