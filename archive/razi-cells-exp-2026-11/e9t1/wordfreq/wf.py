import sys, os, mmap, marshal
from collections import Counter

TABLE = b' ' * 65 + bytes(range(97, 123)) + b' ' * 6 + bytes(range(97, 123)) + b' ' * 133

def count_slice(mm, start, end):
    counts = Counter()
    update = counts.update
    step = 131072
    pos = start
    while pos < end:
        nxt = min(pos + step, end)
        if nxt < end:
            while nxt < end and (65 <= mm[nxt] <= 90 or 97 <= mm[nxt] <= 122):
                nxt += 1
        update(mm[pos:nxt].translate(TABLE).split())
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
        n_workers = 8
        bounds = [0]
        for i in range(1, n_workers):
            p = (size * i) // n_workers
            while p < size and (65 <= mm[p] <= 90 or 97 <= mm[p] <= 122):
                p += 1
            bounds.append(p)
        bounds.append(size)

        pipes = []
        pids = []
        for i in range(1, n_workers):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                c = count_slice(mm, bounds[i], bounds[i+1])
                data = marshal.dumps(dict(c))
                os.write(w, data)
                os.close(w)
                os._exit(0)
            else:
                os.close(w)
                pipes.append(r)
                pids.append(pid)

        counts = count_slice(mm, bounds[0], bounds[1])
        for r in pipes:
            chunks = []
            while b := os.read(r, 65536):
                chunks.append(b)
            os.close(r)
            counts.update(marshal.loads(b"".join(chunks)))
        for pid in pids:
            os.waitpid(pid, 0)
        mm.close()
    else:
        counts = Counter()
        read = sys.stdin.buffer.read
        update = counts.update
        tail = b""
        while chunk := read(131072):
            chunk = tail + chunk.translate(TABLE)
            cut = chunk.rfind(b" ")
            if cut == -1:
                tail = chunk
                continue
            update(chunk[:cut].split())
            tail = chunk[cut+1:]
        if tail:
            update(tail.split())

    top10 = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    sys.stdout.write("".join(f"{w.decode()} {c}\n" for w, c in top10))

if __name__ == '__main__':
    main()
