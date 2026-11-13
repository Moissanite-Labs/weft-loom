import subprocess, time, sys, os
# Score = 1 / (min child CPU seconds, user+sys, over 5 runs). CPU time is used
# instead of wall time because wall time on this machine varied >15% run to run.
exp = open('expected.txt','rb').read()
best = None
for _ in range(5):
    with open('big.txt','rb') as f:
        p = subprocess.Popen([sys.executable, 'wf.py'], stdin=f, stdout=subprocess.PIPE)
        out = p.stdout.read()
        _, status, ru = os.wait4(p.pid, 0)
    if status != 0 or out != exp:
        print(0); sys.exit(0)
    dt = ru.ru_utime + ru.ru_stime
    best = dt if best is None else min(best, dt)
print(round(1.0/best, 3))
