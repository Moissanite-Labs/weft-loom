import sys, os
d = sys.stdin.buffer.read().split()
neg = [t for t in d if t[0] == 45]
r, w = os.pipe()
pid = os.fork()
if pid == 0:
    os.close(r)
    neg.sort(reverse=True); neg.sort(key=len, reverse=True)
    out = b"\n".join(neg) + b"\n"
    os.write(1, out)
    os._exit(0)
os.close(w)
pos = [t for t in d if t[0] != 45]
pos.sort(); pos.sort(key=len)
out = b"\n".join(pos) + b"\n"
os.waitpid(pid, 0)
os.write(1, out)
