import os
import sys
import pickle


def core(body):
    t = body.replace(b'.', b'').replace(b'\n', b',')
    f = t.split(b',')
    sums = {}
    get = sums.get
    for c, v in zip(f[1::3], f[2::3]):
        if v:
            sums[c] = get(c, 0) + int(v)
    return sums


def fmt(sums):
    out = []
    ap = out.append
    for c in sorted(sums):
        v = sums[c]
        if v < 0:
            v = -v
            ap(b"%s -%d.%02d\n" % (c, v // 100, v % 100))
        else:
            ap(b"%s %d.%02d\n" % (c, v // 100, v % 100))
    return b"".join(out)


def nprocs():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count() or 1
    except Exception:
        return 1


def parallel(body):
    L = len(body)
    n = nprocs()
    if L < 262144 or n <= 1:
        return core(body)
    step = max(1, L // n)
    bounds = [0]
    p = 0
    for i in range(1, n):
        p += step
        if p >= L:
            break
        q = body.find(b'\n', p)
        bounds.append(L if q < 0 else q + 1)
    bounds.append(L)
    pipes = []
    pids = []
    for i in range(len(bounds) - 1):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                d = pickle.dumps(core(body[bounds[i]:bounds[i + 1]]), 2)
                while d:
                    d = d[os.write(w, d):]
            finally:
                os._exit(0)
        os.close(w)
        pipes.append(r)
        pids.append(pid)
    sums = {}
    get = sums.get
    for r in pipes:
        chunks = []
        while True:
            b = os.read(r, 1 << 16)
            if not b:
                break
            chunks.append(b)
        os.close(r)
        for k, v in pickle.loads(b''.join(chunks)).items():
            sums[k] = get(k, 0) + v
    for pid in pids:
        os.waitpid(pid, 0)
    return sums


def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b'\n')
    if nl < 0:
        return
    body = data[nl + 1:]
    if b'\r' in body:
        body = body.replace(b'\r', b'')
    try:
        sums = parallel(body)
    except OSError:
        sums = core(body)
    sys.stdout.buffer.write(fmt(sums))


main()
