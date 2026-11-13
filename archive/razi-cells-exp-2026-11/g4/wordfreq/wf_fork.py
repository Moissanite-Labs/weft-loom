import sys, os, pickle
from collections import Counter

_table = bytearray(range(256))
for _c in range(256):
    if 65 <= _c <= 90:
        _table[_c] = _c + 32
    elif 97 <= _c <= 122:
        _table[_c] = _c
    else:
        _table[_c] = 32
TABLE = bytes(_table)


def emit(counts):
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    if top:
        sys.stdout.write("\n".join("%s %d" % (w.decode("ascii"), c) for w, c in top) + "\n")


def main():
    data = sys.stdin.buffer.read()
    tr = data.translate(TABLE)
    n = len(tr)
    ncpu = min(8, os.cpu_count() or 1)
    if n < 4_000_000 or ncpu < 2:
        emit(Counter(tr.split()))
        return
    bounds = [0]
    for i in range(1, ncpu):
        pos = n * i // ncpu
        if pos <= bounds[-1]:
            continue
        sp = tr.find(b' ', pos)
        if sp < 0:
            break
        bounds.append(sp + 1)
    bounds.append(n)
    nch = len(bounds) - 1
    if nch < 2:
        emit(Counter(tr.split()))
        return
    chunks = [tr[bounds[i]:bounds[i + 1]] for i in range(nch)]
    del tr, data
    procs = []
    for ch in chunks:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(r)
                c = Counter(ch.split())
                with os.fdopen(w, 'wb') as f:
                    pickle.dump(dict(c), f, 2)
            except BaseException:
                os._exit(1)
            os._exit(0)
        os.close(w)
        procs.append((pid, r))
    total = Counter()
    for pid, r in procs:
        try:
            with os.fdopen(r, 'rb') as f:
                total.update(pickle.load(f))
        except Exception:
            pass
        try:
            os.waitpid(pid, 0)
        except Exception:
            pass
    emit(total)


main()
