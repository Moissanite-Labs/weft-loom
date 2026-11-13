import sys, os
from collections import Counter

# non-letters -> space, uppercase -> lowercase (ASCII words [a-z]+)
_T = bytes((c if 97 <= c <= 122 else c + 32 if 65 <= c <= 90 else 32) for c in range(256))

def main():
    data = sys.stdin.buffer.read().translate(_T)
    n = len(data)
    try:
        ncpu = len(os.sched_getaffinity(0))
    except Exception:
        ncpu = os.cpu_count() or 1
    k = int(os.environ.get("WF_N", 0)) or min(ncpu, 8)
    c = None
    if k > 1 and n > 2000000 and hasattr(os, "fork"):
        import marshal
        cuts = [0]
        for i in range(1, k):
            p = data.find(b" ", max(n * i // k, cuts[-1]))
            cuts.append(n if p < 0 else p)
        cuts.append(n)
        kids = []
        try:
            for i in range(1, k):
                r, w = os.pipe()
                pid = os.fork()
                if pid == 0:
                    code = 1
                    try:
                        os.close(r)
                        d = dict(Counter(data[cuts[i]:cuts[i + 1]].split()))
                        with os.fdopen(w, "wb") as f:
                            f.write(marshal.dumps(d))
                        code = 0
                    finally:
                        os._exit(code)
                os.close(w)
                kids.append((pid, r))
            c = Counter(data[:cuts[1]].split())
            ok = True
            for pid, r in kids:
                with os.fdopen(r, "rb") as f:
                    buf = f.read()
                _, st = os.waitpid(pid, 0)
                if st != 0:
                    ok = False
                else:
                    c.update(marshal.loads(buf))
            if not ok:
                c = None
        except OSError:
            c = None
    if c is None:
        c = Counter(data.split())
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join("%s %d\n" % (w.decode(), n) for w, n in top))

main()
