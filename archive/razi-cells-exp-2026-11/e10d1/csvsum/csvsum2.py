#!/usr/bin/env python3
import sys, os, stat
from decimal import Decimal

def parse_milli(v):
    neg = v[:1] == b'-'
    if neg:
        v = v[1:]
    k = v.find(b'.')
    if k < 0:
        n = int(v) * 1000
    else:
        frac = v[k + 1:]
        if len(frac) > 3:
            d = Decimal(v.decode()).quantize(Decimal('0.001'))
            n = int(d * 1000)
        else:
            whole = v[:k]
            n = (int(whole) if whole else 0) * 1000 + (int(frac.ljust(3, b'0')) if frac else 0)
    return -n if neg else n

def summarize(body):
    sums = {}
    get = sums.get
    for line in body.split(b'\n'):
        if not line:
            continue
        i = line.find(b',')
        j = line.find(b',', i + 1)
        cat = line[i + 1:j]
        v = line[j + 1:]
        k = v.find(b'.')
        if k >= 0 and len(v) - k == 4:
            n = int(v[:k] + v[k + 1:])
        else:
            n = parse_milli(v.strip())
        sums[cat] = get(cat, 0) + n
    return sums

def emit(sums):
    out = sys.stdout
    q = Decimal('0.01')
    lines = []
    for cat in sorted(sums):
        d = (Decimal(sums[cat]) / 1000).quantize(q)
        lines.append("%s,%s\n" % (cat.decode(), d))
    out.write("".join(lines))

def serial():
    data = sys.stdin.buffer.read()
    nl = data.find(b'\n')
    if nl < 0:
        return
    emit(summarize(data[nl + 1:]))

def main():
    try:
        st = os.fstat(0)
        size = st.st_size
        regular = stat.S_ISREG(st.st_mode)
    except OSError:
        regular = False
    if not regular or size < 4_000_000 or not hasattr(os, 'fork'):
        return serial()
    head = os.pread(0, 4096, 0)
    nl = head.find(b'\n')
    if nl < 0:
        return
    start0 = nl + 1
    nproc = min(8, os.cpu_count() or 1)
    bounds = [start0]
    for i in range(1, nproc):
        b = start0 + (size - start0) * i // nproc
        chunk = os.pread(0, 256, b)
        k = chunk.find(b'\n')
        bounds.append(b + k + 1 if k >= 0 else size)
    bounds.append(size)
    pipes = []
    for i in range(nproc):
        s, e = bounds[i], bounds[i + 1]
        if e <= s:
            continue
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            data = os.pread(0, e - s, s)
            d = summarize(data)
            payload = b"".join(b"%s %d\n" % (c, n) for c, n in d.items())
            os.write(w, payload)
            os._exit(0)
        os.close(w)
        pipes.append((pid, r))
    sums = {}
    for pid, r in pipes:
        buf = []
        while True:
            chunk = os.read(r, 65536)
            if not chunk:
                break
            buf.append(chunk)
        os.close(r)
        os.waitpid(pid, 0)
        for line in b"".join(buf).split(b'\n'):
            if line:
                c, n = line.rsplit(b' ', 1)
                sums[c] = sums.get(c, 0) + int(n)
    emit(sums)

if __name__ == '__main__':
    main()
