import sys, os
from pickle import dumps, loads

def slow(chunk):
    d = {}
    get = d.get
    for line in chunk.split(b'\n'):
        line = line.strip()
        if line:
            _, c, v = line.split(b',')
            d[c] = get(c, 0.0) + float(v)
    return d

def work(chunk):
    parts = chunk.replace(b'\n', b',').split(b',')
    if len(parts) % 3:
        return slow(chunk)
    d = {}
    get = d.get
    try:
        for c, v in zip(parts[1::3], map(float, parts[2::3])):
            d[c] = get(c, 0.0) + v
    except ValueError:
        return slow(chunk)
    return d

def main():
    data = sys.stdin.buffer.read()
    n = len(data)
    start = data.find(b'\n') + 1
    if start == 0:
        return
    N = int(os.environ.get('CSVSUM_N', 0)) or min(NDEF, os.cpu_count() or 1)
    if n - start < 1 << 20 or not hasattr(os, 'fork'):
        N = 1
    bounds = [start]
    for i in range(1, N):
        p = data.find(b'\n', start + (n - start) * i // N)
        if p < 0:
            break
        if p + 1 > bounds[-1]:
            bounds.append(p + 1)
    bounds.append(n)
    kids = []
    for i in range(len(bounds) - 2):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                b = dumps(work(data[bounds[i]:bounds[i + 1]].rstrip(b'\n')))
                os.write(w, b)
                os.close(w)
                os._exit(0)
            except BaseException:
                os._exit(1)
        os.close(w)
        kids.append((pid, r))
    last = work(data[bounds[-2]:bounds[-1]].rstrip(b'\n'))
    tot = {}
    get = tot.get
    parts = []
    for pid, r in kids:
        with os.fdopen(r, 'rb') as f:
            b = f.read()
        _, st = os.waitpid(pid, 0)
        if st != 0:
            sys.exit(1)
        parts.append(loads(b))
    parts.append(last)
    for d in parts:
        for k, v in d.items():
            tot[k] = get(k, 0.0) + v
    sys.stdout.write(''.join(['%s,%.2f\n' % (k.decode(), tot[k]) for k in sorted(tot)]))
NDEF = 16
main()
