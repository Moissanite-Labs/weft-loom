import sys, os, mmap, marshal
from io import BytesIO

def work(chunk):
    sums = {}
    fl = float
    for line in BytesIO(chunk):
        _, cat, val = line.split(b',')
        try:
            sums[cat] += fl(val)
        except KeyError:
            sums[cat] = fl(val)
    return sums

def main():
    try:
        mm = mmap.mmap(0, 0, access=mmap.ACCESS_READ)
    except Exception:
        mm = sys.stdin.buffer.read()
    n = len(mm)
    start0 = mm.find(b'\n') + 1
    W = 8
    bounds = [start0]
    for i in range(1, W):
        pos = start0 + (n - start0) * i // W
        nl = mm.find(b'\n', pos)
        bounds.append(nl + 1 if nl != -1 else n)
    bounds.append(n)

    children = []
    for i in range(1, W):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            s = work(mm[bounds[i]:bounds[i+1]])
            os.write(w, marshal.dumps(s))
            os.close(w)
            os._exit(0)
        else:
            os.close(w)
            children.append((r, pid))

    sums = work(mm[bounds[0]:bounds[1]])
    for r, pid in children:
        buf = b''.join(iter(lambda: os.read(r, 65536), b''))
        os.close(r)
        os.waitpid(pid, 0)
        for k, v in marshal.loads(buf).items():
            sums[k] = sums.get(k, 0.0) + v

    out = [f"{cat.decode()},{sums[cat]:.2f}\n" for cat in sorted(sums)]
    sys.stdout.write("".join(out))

if __name__ == '__main__':
    main()
