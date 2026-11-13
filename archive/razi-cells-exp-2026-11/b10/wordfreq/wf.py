import os, sys, mmap, pickle
from collections import Counter

def count_range(mm, start, end):
    counts = Counter()
    update = counts.update
    CHUNK = 262144
    pos = start
    while pos < end:
        nxt = min(pos + CHUNK, end)
        if nxt < end:
            while nxt < end and mm[nxt] > 32:
                nxt += 1
        update(mm[pos:nxt].split())
        pos = nxt
    return counts

def main():
    try:
        st = os.fstat(0)
        size = st.st_size
    except Exception:
        size = 0

    if size > 1_000_000:
        mm = mmap.mmap(0, size, access=mmap.ACCESS_READ)
        nworkers = 6
        step = size // nworkers
        bounds = [0]
        for i in range(1, nworkers):
            p = i * step
            while p < size and mm[p] > 32:
                p += 1
            bounds.append(p)
        bounds.append(size)

        pipes = []
        pids = []
        for i in range(1, nworkers):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                c = count_range(mm, bounds[i], bounds[i+1])
                data = pickle.dumps(dict(c), protocol=-1)
                os.write(w, data)
                os.close(w)
                os._exit(0)
            else:
                os.close(w)
                pipes.append(r)
                pids.append(pid)

        total = count_range(mm, bounds[0], bounds[1])
        for r in pipes:
            chunks = []
            while True:
                b = os.read(r, 65536)
                if not b:
                    break
                chunks.append(b)
            os.close(r)
            d = pickle.loads(b"".join(chunks))
            for k, v in d.items():
                total[k] += v
        for pid in pids:
            os.waitpid(pid, 0)
        mm.close()
    else:
        total = Counter(sys.stdin.buffer.read().split())

    lower_counts = Counter()
    for w, c in total.items():
        lower_counts[w.lower()] += c
    top10 = sorted(lower_counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    for w, c in top10:
        print(f"{w.decode('utf-8')} {c}")

if __name__ == "__main__":
    main()
