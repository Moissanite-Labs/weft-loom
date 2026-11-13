import sys, os, collections
tbl = bytes((c + 32) if 65 <= c <= 90 else (c if (48 <= c <= 57 or 97 <= c <= 122 or c == 95) else 32) for c in range(256))
fd = 0
try:
    L = os.fstat(fd).st_size
    os.pread(fd, 1, 0)
    seekable = L > 0
except Exception:
    seekable = False
n = max(1, os.cpu_count() or 1)
if not seekable:
    data = sys.stdin.buffer.read()
    L = len(data)
    def getchunk(i):
        s = L * i // n; e = L * (i + 1) // n
        if i > 0:
            p = data.find(b'\n', s); s = L if p < 0 else p + 1
        if i < n - 1:
            p = data.find(b'\n', e); e = L if p < 0 else p + 1
        return data[s:e]
else:
    def getchunk(i):
        s = L * i // n; e = L * (i + 1) // n
        raw = os.pread(fd, e - s + 65536, s)
        a = 0
        if i > 0:
            p = raw.find(b'\n'); a = len(raw) if p < 0 else p + 1
        b = len(raw)
        if i < n - 1:
            p = raw.find(b'\n', e - s); b = len(raw) if p < 0 else p + 1
        return raw[a:b]
pipes = []
for i in range(n):
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        c = collections.Counter(getchunk(i).translate(tbl).split())
        out = b''.join(b'%s %d\n' % kv for kv in c.items())
        with os.fdopen(w, 'wb') as f:
            f.write(out)
        os._exit(0)
    os.close(w)
    pipes.append(r)
total = {}
g = total.get
for r in pipes:
    with os.fdopen(r, 'rb') as f:
        for line in f.read().split(b'\n'):
            if line:
                w_, c_ = line.rsplit(b' ', 1)
                total[w_] = g(w_, 0) + int(c_)
top = sorted(total.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
sys.stdout.write("".join(f"{w.decode()} {n}\n" for w, n in top))
