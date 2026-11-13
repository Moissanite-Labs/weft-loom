import sys
import os
import re
import ctypes

def main():
    try:
        lib = ctypes.CDLL("./libfastcsv.dylib")
        fn = None
        for name in ("process_stdin", "run_csvsum", "fast_csvsum", "process_csv", "csvsum", "run", "process"):
            fn = getattr(lib, name, None)
            if fn is not None:
                break
        if fn is None:
            names = re.findall(r"^\s*(?:int|void)\s+([a-zA-Z_]\w*)\s*\(", open("fastcsv.c").read(), re.M)
            if names:
                fn = getattr(lib, names[-1], None)
        if fn is not None:
            res = fn(0, 1)
            if res == 0:
                return
    except Exception:
        pass

    import mmap, pickle
    def process_chunk(data):
        sums = {}
        for line in data.splitlines():
            if line:
                _, cat, val = line.split(b',')
                try:
                    sums[cat] += float(val)
                except KeyError:
                    sums[cat] = float(val)
        return sums

    fd = sys.stdin.fileno()
    size = os.fstat(fd).st_size
    mm = mmap.mmap(fd, size, access=mmap.ACCESS_READ)
    first_nl = mm.find(b'\n') + 1
    n_workers = 8
    step = (size - first_nl) // n_workers
    ranges = []
    cur = first_nl
    for i in range(n_workers):
        nxt = size if i == n_workers - 1 else mm.find(b'\n', cur + step) + 1
        if nxt == 0:
            nxt = size
        if cur < nxt:
            ranges.append((cur, nxt))
        cur = nxt

    rpipes = []
    pids = []
    for s, e in ranges[1:]:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            res = process_chunk(mm[s:e])
            with os.fdopen(w, 'wb') as wf:
                pickle.dump(res, wf)
            os._exit(0)
        else:
            os.close(w)
            rpipes.append(r)
            pids.append(pid)

    total = process_chunk(mm[ranges[0][0]:ranges[0][1]])
    for r, pid in zip(rpipes, pids):
        with os.fdopen(r, 'rb') as rf:
            sub = pickle.load(rf)
        os.waitpid(pid, 0)
        for k, v in sub.items():
            total[k] = total.get(k, 0.0) + v

    mm.close()
    out = sys.stdout.write
    for cat in sorted(total):
        out(f"{cat.decode()},{total[cat]:.2f}\n")

if __name__ == '__main__':
    main()
