import sys, os, marshal
N = int('16')
def work(chunk):
    parts = chunk.replace(b'\n', b',').split(b',')
    d = {}
    g = d.get
    for c, v in zip(parts[1::3], map(float, parts[2::3])):
        d[c] = g(c, 0.0) + v
    return d
def main():
    data = None
    try:
        import stat
        st = os.fstat(0)
        if stat.S_ISREG(st.st_mode) and st.st_size > 0:
            import mmap
            data = mmap.mmap(0, st.st_size, access=mmap.ACCESS_READ)
    except Exception:
        data = None
    if data is None:
        data = sys.stdin.buffer.read()
    n = len(data)
    start = data.find(b'\n') + 1
    if start == 0:
        return
    if n - start < (1 << 18) or N < 2:
        d = work(data[start:n])
    else:
        b = [start]
        for i in range(1, N):
            p = start + (n - start) * i // N
            q = data.find(b'\n', p)
            b.append(n if q < 0 else q + 1)
        b.append(n)
        kids = []
        for i in range(N - 1):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                try:
                    os.close(r)
                    s = marshal.dumps(work(data[b[i]:b[i + 1]]))
                    mv = memoryview(s)
                    while mv:
                        k = os.write(w, mv)
                        mv = mv[k:]
                    os._exit(0)
                except BaseException:
                    os._exit(1)
            os.close(w)
            kids.append((pid, r))
        d = work(data[b[N - 1]:b[N]])
        g = d.get
        for pid, r in kids:
            buf = []
            while True:
                x = os.read(r, 1 << 20)
                if not x:
                    break
                buf.append(x)
            os.close(r)
            os.waitpid(pid, 0)
            for k, v in marshal.loads(b''.join(buf)).items():
                d[k] = g(k, 0.0) + v
    sys.stdout.write(''.join(['%s,%.2f\n' % (k.decode(), d[k]) for k in sorted(d)]))
main()
