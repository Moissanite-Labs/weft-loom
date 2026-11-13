import sys, os, gc

gc.disable()
data = sys.stdin.buffer.read().split()
n = len(data)
if n < 50000:
    if n:
        data.sort(key=int)
        data.append(b"")
        sys.stdout.buffer.write(b"\n".join(data))
        sys.stdout.buffer.flush()
    os._exit(0)

# 2-way fork writing directly to stdout in order (child writes neg to stdout first? No, parent sorts pos while child sorts neg and writes to stdout!)
pid = os.fork()
if pid == 0:
    neg = [x for x in data if x[0] == 45]
    neg.sort(key=int)
    if neg:
        neg.append(b"")
        sys.stdout.buffer.write(b"\n".join(neg))
        sys.stdout.buffer.flush()
    os._exit(0)
else:
    pos = [x for x in data if x[0] != 45]
    pos.sort(key=int)
    if pos:
        pos.append(b"")
        pos_bytes = b"\n".join(pos)
    else:
        pos_bytes = b""
    os.waitpid(pid, 0)
    if pos_bytes:
        sys.stdout.buffer.write(pos_bytes)
        sys.stdout.buffer.flush()
    os._exit(0)
