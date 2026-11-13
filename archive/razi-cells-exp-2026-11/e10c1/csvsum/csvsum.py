import sys, os, pickle

W = 10

def work(chunk):
    parts = chunk.replace(b"\n", b",").split(b",")
    if parts and parts[-1] == b"":
        parts.pop()
    sums = {}
    g = sums.get
    for c, v in zip(parts[1::3], map(float, parts[2::3])):
        sums[c] = g(c, 0.0) + v
    return sums

def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b"\n")
    start = nl + 1
    n = len(data)
    bounds = [start]
    for i in range(1, W):
        pos = data.find(b"\n", start + (n - start) * i // W)
        bounds.append(n if pos < 0 else pos + 1)
    bounds.append(n)
    pipes = []
    for i in range(W):
        a, b = bounds[i], bounds[i + 1]
        if a >= b:
            continue
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            res = pickle.dumps(work(data[a:b]), protocol=pickle.HIGHEST_PROTOCOL)
            while res:
                k = os.write(w, res)
                res = res[k:]
            os._exit(0)
        os.close(w)
        pipes.append((pid, r))
    total = {}
    for pid, r in pipes:
        buf = b""
        while True:
            c = os.read(r, 65536)
            if not c:
                break
            buf += c
        os.close(r)
        os.waitpid(pid, 0)
        g = total.get
        for k, v in pickle.loads(buf).items():
            total[k] = g(k, 0.0) + v
    sys.stdout.write("".join("%s,%.2f\n" % (k.decode(), v) for k, v in sorted(total.items())))

main()
