import sys, os, pickle
from collections import Counter

_TBL = bytes(c + 32 if 65 <= c <= 90 else (c if 97 <= c <= 122 else 32) for c in range(256))

def count(data, i, j):
    return Counter(data[i:j].translate(_TBL).split())

def main():
    data = sys.stdin.buffer.read()
    n = len(data)
    nw = min(os.cpu_count() or 1, 16)
    if n < (1 << 20) or nw < 2:
        c = count(data, 0, n)
    else:
        bounds = [0]
        for k in range(1, nw):
            j = n * k // nw
            while j < n and (97 <= data[j] <= 122 or 65 <= data[j] <= 90):
                j += 1
            bounds.append(j)
        bounds.append(n)
        pipes = []
        for k in range(nw):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                res = pickle.dumps(dict(count(data, bounds[k], bounds[k + 1])), pickle.HIGHEST_PROTOCOL)
                with os.fdopen(w, 'wb') as f:
                    f.write(res)
                os._exit(0)
            os.close(w)
            pipes.append((pid, r))
        c = Counter()
        for pid, r in pipes:
            with os.fdopen(r, 'rb') as f:
                c.update(pickle.load(f))
            os.waitpid(pid, 0)
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join(f"{w.decode()} {n}\n" for w, n in top))

if __name__ == "__main__":
    main()
