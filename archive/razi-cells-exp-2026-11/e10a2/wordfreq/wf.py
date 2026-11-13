import sys, os, marshal
from collections import Counter

NP = min(8, os.cpu_count() or 2)

# Map A-Z -> a-z, keep a-z, everything else -> space.
_T = bytearray(b' ' * 256)
for _c in range(26):
    _T[65 + _c] = 97 + _c
    _T[97 + _c] = 97 + _c
_T = bytes(_T)


def count(data):
    # children translate their own raw slice; boundaries are placed on a
    # non-letter byte of the raw data so no word is cut.
    n = len(data)
    if n < (1 << 20) or not hasattr(os, 'fork') or NP < 2:
        return Counter(data.translate(_T).split())
    bounds = [0]
    for i in range(1, NP):
        p = n * i // NP
        while p < n and _T[data[p]] != 32:
            p += 1
        bounds.append(p)
    bounds.append(n)
    kids = []
    for i in range(1, NP):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            code = 1
            try:
                os.close(r)
                c = Counter(data[bounds[i]:bounds[i + 1]].translate(_T).split())
                with os.fdopen(w, 'wb') as f:
                    f.write(marshal.dumps(dict(c)))
                code = 0
            finally:
                os._exit(code)
        os.close(w)
        kids.append((pid, r))
    counts = Counter(data[bounds[0]:bounds[1]].translate(_T).split())
    for pid, r in kids:
        with os.fdopen(r, 'rb') as f:
            d = marshal.loads(f.read())
        os.waitpid(pid, 0)
        counts.update(d)
    return counts


def main():
    data = sys.stdin.buffer.read()
    counts = count(data)
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    out = sys.stdout
    for w, c in top:
        out.write('%s %d\n' % (w.decode('ascii'), c))


if __name__ == '__main__':
    main()
