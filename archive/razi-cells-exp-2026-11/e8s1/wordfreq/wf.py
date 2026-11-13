import sys, os, gc, marshal
from collections import Counter

TRANS = bytes(i + 32 if 65 <= i <= 90 else (i if 97 <= i <= 122 else 32) for i in range(256))

def is_alpha(b):
    return 65 <= b <= 90 or 97 <= b <= 122

def count_range(fd, start, end):
    counts = Counter()
    pos = start
    step = 2 * 1024 * 1024
    rem = b""
    while pos < end:
        to_read = min(step, end - pos)
        chunk = os.pread(fd, to_read, pos)
        if not chunk:
            break
        pos += len(chunk)
        chunk = rem + chunk
        if pos < end:
            idx = len(chunk) - 1
            while idx >= 0 and (65 <= chunk[idx] <= 90 or 97 <= chunk[idx] <= 122):
                idx -= 1
            rem = chunk[idx+1:]
            chunk = chunk[:idx+1]
        else:
            rem = b""
        counts.update(chunk.translate(TRANS).split())
    if rem:
        counts.update(rem.translate(TRANS).split())
    return counts

def main():
    gc.disable()
    fd = sys.stdin.fileno()
    try:
        size = os.fstat(fd).st_size
    except Exception:
        size = 0
    if size > 4_000_000 and hasattr(os, "pread") and hasattr(os, "fork"):
        n_workers = 6
        bounds = [0]
        for i in range(1, n_workers):
            p = (size * i) // n_workers
            buf = os.pread(fd, 256, p)
            offset = 0
            while offset < len(buf) and is_alpha(buf[offset]):
                offset += 1
            bounds.append(p + offset)
        bounds.append(size)

        pipes = []
        pids = []
        for i in range(1, n_workers):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                c = count_range(fd, bounds[i], bounds[i+1])
                data = marshal.dumps(dict(c))
                os.write(w, data)
                os.close(w)
                os._exit(0)
            else:
                os.close(w)
                pipes.append(r)
                pids.append(pid)

        total = count_range(fd, bounds[0], bounds[1])
        for r in pipes:
            chunks = []
            while True:
                b = os.read(r, 65536)
                if not b:
                    break
                chunks.append(b)
            os.close(r)
            total.update(marshal.loads(b"".join(chunks)))
        for pid in pids:
            os.waitpid(pid, 0)
        counts = total
    else:
        counts = Counter(sys.stdin.buffer.read().translate(TRANS).split())

    top = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    sys.stdout.write("".join(f"{w.decode('ascii')} {c}\n" for w, c in top))

if __name__ == '__main__':
    main()
