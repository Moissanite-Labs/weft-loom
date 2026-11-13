import sys, os

def sum_chunk(buf):
    from collections import defaultdict
    sums = defaultdict(float)
    lines = buf.decode('ascii', 'replace').split('\n')
    for ln in lines:
        if not ln:
            continue
        _, c, v = ln.split(',', 2)
        sums[c] += float(v)
    return sums

def main():
    buf = sys.stdin.buffer.read()
    # strip header
    nl = buf.find(b'\n')
    if nl >= 0 and buf[:nl].startswith(b'id,'):
        buf = buf[nl + 1:]
    try:
        ncpu = len(os.sched_getaffinity(0))
    except Exception:
        ncpu = os.cpu_count() or 1
    ncpu = max(1, min(ncpu, 16))
    n = len(buf)
    if ncpu == 1 or n < 1 << 20 or not hasattr(os, 'fork'):
        total = sum_chunk(buf)
    else:
        # chunk boundaries on newlines
        bounds = [0]
        for i in range(1, ncpu):
            p = buf.find(b'\n', n * i // ncpu)
            bounds.append(n if p < 0 else p + 1)
        bounds.append(n)
        import marshal
        pids = []
        for i in range(ncpu):
            lo, hi = bounds[i], bounds[i + 1]
            if hi <= lo:
                continue
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                try:
                    d = dict(sum_chunk(buf[lo:hi]))
                    data = marshal.dumps(d)
                    with os.fdopen(w, 'wb') as f:
                        f.write(data)
                finally:
                    os._exit(0)
            os.close(w)
            pids.append((pid, r))
        total = {}
        for pid, r in pids:
            with os.fdopen(r, 'rb') as f:
                data = f.read()
            os.waitpid(pid, 0)
            for k, v in marshal.loads(data).items():
                total[k] = total.get(k, 0.0) + v
    out = []
    for c in sorted(total):
        out.append("%s,%.2f" % (c, total[c]))
    sys.stdout.write("\n".join(out) + "\n")

main()
