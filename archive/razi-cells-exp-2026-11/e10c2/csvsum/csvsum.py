import sys, os, stat

def work(chunk):
    parts = chunk.replace(b"\n", b",").split(b",")
    sums = {}
    for c, v in zip(parts[1::3], map(float, parts[2::3])):
        try:
            sums[c] += v
        except KeyError:
            sums[c] = v
    return sums

def run(N, loader):
    procs = []
    for i in range(N - 1):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            d = work(loader(i))
            os.write(w, b"\n".join(k + b"," + repr(v).encode() for k, v in d.items()))
            os._exit(0)
        os.close(w)
        procs.append((pid, r))
    total = work(loader(N - 1))
    for pid, r in procs:
        chunks = []
        while True:
            b = os.read(r, 65536)
            if not b:
                break
            chunks.append(b)
        os.close(r)
        os.waitpid(pid, 0)
        for line in b"".join(chunks).split(b"\n"):
            if line:
                k, v = line.rsplit(b",", 1)
                total[k] = total.get(k, 0.0) + float(v)
    out = ["%s,%.2f" % (k.decode(), total[k]) for k in sorted(total)]
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

def main():
    N = max(1, min(16, os.cpu_count() or 1))
    fd = 0
    size = -1
    try:
        st = os.fstat(fd)
        if stat.S_ISREG(st.st_mode):
            size = st.st_size
    except OSError:
        pass
    if size > 0:
        def boundary(p):
            if p >= size:
                return size
            off = p
            while True:
                buf = os.pread(fd, 1024, off)
                if not buf:
                    return size
                j = buf.find(b"\n")
                if j >= 0:
                    return off + j + 1
                off += len(buf)
        bounds = [(size * i) // N for i in range(N + 1)]
        def loader(i):
            a = boundary(bounds[i]); b = boundary(bounds[i + 1])
            parts = []
            while a < b:
                buf = os.pread(fd, b - a, a)
                if not buf:
                    break
                parts.append(buf); a += len(buf)
            return b"".join(parts)
        run(N, loader)
    else:
        data = sys.stdin.buffer.read()
        nl = data.find(b"\n")
        body = data[nl + 1:] if nl >= 0 else b""
        L = len(body)
        bounds = [0]
        for i in range(1, N):
            p = body.find(b"\n", (L * i) // N)
            bounds.append(L if p < 0 else p + 1)
        bounds.append(L)
        run(N, lambda i: body[bounds[i]:bounds[i + 1]])

main()
