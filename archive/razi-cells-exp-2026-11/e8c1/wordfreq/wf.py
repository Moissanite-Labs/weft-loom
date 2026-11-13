import os
import sys
import mmap
import heapq
import pickle
from collections import Counter

_TRANS = (
    b"                                "
    b"                                "
    b" abcdefghijklmnopqrstuvwxyz     "
    b" abcdefghijklmnopqrstuvwxyz     "
    + b" " * 128
)

def _count_range(mm, start, end):
    counts = Counter()
    update = counts.update
    pos = start
    step = 262144
    trans = _TRANS
    while pos < end:
        nxt = pos + step
        if nxt >= end:
            nxt = end
        else:
            while nxt < end and trans[mm[nxt]] != 32:
                nxt += 1
        update(mm[pos:nxt].translate(trans).split())
        pos = nxt
    return counts

def main():
    counts = None
    try:
        st = os.fstat(0)
        size = st.st_size
        if size > 1_000_000:
            mm = mmap.mmap(0, size, access=mmap.ACCESS_READ)
            nworkers = min(8, os.cpu_count() or 4)
            bounds = [0]
            for i in range(1, nworkers):
                p = (size * i) // nworkers
                if p < bounds[-1]:
                    p = bounds[-1]
                while p < size and _TRANS[mm[p]] != 32:
                    p += 1
                bounds.append(p)
            bounds.append(size)
            pipes = []
            pids = []
            for i in range(1, nworkers):
                rfd, wfd = os.pipe()
                pid = os.fork()
                if pid == 0:
                    os.close(rfd)
                    c = _count_range(mm, bounds[i], bounds[i + 1])
                    data = pickle.dumps(dict(c), protocol=-1)
                    mv = memoryview(data)
                    written = 0
                    while written < len(data):
                        written += os.write(wfd, mv[written:])
                    os.close(wfd)
                    os._exit(0)
                else:
                    os.close(wfd)
                    pipes.append(rfd)
                    pids.append(pid)
            counts = _count_range(mm, bounds[0], bounds[1])
            for rfd in pipes:
                chunks = []
                while True:
                    b = os.read(rfd, 65536)
                    if not b:
                        break
                    chunks.append(b)
                os.close(rfd)
                counts.update(pickle.loads(b"".join(chunks)))
            for pid in pids:
                os.waitpid(pid, 0)
            mm.close()
    except Exception:
        counts = None

    if counts is None:
        counts = Counter()
        update = counts.update
        rem = b""
        while True:
            chunk = os.read(0, 262144)
            if not chunk:
                if rem:
                    update(rem.split())
                break
            t = rem + chunk.translate(_TRANS)
            idx = t.rfind(b" ")
            if idx == -1:
                rem = t
            else:
                rem = t[idx + 1:]
                update(t[:idx].split())

    if not counts:
        return
    if len(counts) > 10:
        thresh = heapq.nlargest(10, counts.values())[-1]
        cands = [(-c, w) for w, c in counts.items() if c >= thresh]
        cands.sort()
        top10 = cands[:10]
    else:
        top10 = sorted((-c, w) for w, c in counts.items())
    sys.stdout.write("\n".join(f"{w.decode()} {-neg_c}" for neg_c, w in top10) + "\n")

if __name__ == "__main__":
    main()
