import sys, os
d = sys.stdin.buffer.read().split()
n10 = [t for t in d if t[0] == 45 and len(t) == 11]
n9 = [t for t in d if t[0] == 45 and len(t) != 11]
p9 = [t for t in d if t[0] != 45 and len(t) != 10]
p10 = [t for t in d if t[0] != 45 and len(t) == 10]
del d
def work(g, desc):
    g.sort(reverse=desc); g.sort(key=len, reverse=desc)
    return b"\n".join(g) + b"\n"
def wall(fd, b):
    v = memoryview(b)
    while v:
        k = os.write(fd, v); v = v[k:]
groups = [(n10, True), (n9, True), (p9, False), (p10, False)]
pipes = []
for g, desc in groups[:3]:
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        wall(w, work(g, desc))
        os._exit(0)
    os.close(w)
    pipes.append((r, pid))
last = work(*groups[3])
for r, pid in pipes:
    with open(r, 'rb', buffering=1<<20) as f:
        wall(1, f.read())
    os.waitpid(pid, 0)
wall(1, last)
