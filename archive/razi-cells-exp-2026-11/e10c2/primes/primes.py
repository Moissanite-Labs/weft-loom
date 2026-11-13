import sys, os

R = (1, 7, 11, 13, 17, 19, 23, 29)
INV = {r: pow(r, -1, 30) for r in R}
PIECES = 2


def small_primes(limit):
    size = limit // 2 + 1
    s = bytearray([1]) * size
    s[0] = 0
    i = 1
    while True:
        p = 2 * i + 1
        if p * p > limit:
            break
        if s[i]:
            st = p * p // 2
            s[st::p] = bytes(len(range(st, size, p)))
        i += 1
    return [2 * i + 1 for i in range(3, size) if s[i]]


def work(n, primes, zeros, j, lo, hi):
    t = R[j]
    L = hi - lo
    arr = bytearray([1]) * L
    if j == 0 and lo == 0:
        arr[0] = 0
    k = (n - t + 29) // 30
    if k < hi:
        kk = k if k > lo else lo
        arr[kk - lo:] = bytes(hi - kk)
    for p in primes:
        if p * p // 30 >= hi:
            break
        q = (t * INV[p % 30]) % 30
        m = p + ((q - p) % 30)
        idx = (p * m) // 30
        if idx < lo:
            idx += ((lo - idx + p - 1) // p) * p
        if idx >= hi:
            continue
        arr[idx - lo::p] = zeros[:(hi - idx + p - 1) // p]
    return arr.count(1)


def count_primes(n):
    if n < 3:
        return 0
    if n <= 7:
        return sum(1 for p in (2, 3, 5, 7) if p < n)
    primes = small_primes(int(n ** 0.5) + 1)
    size = n // 30 + 1
    zeros = memoryview(bytes(size // 7 + 2))
    tasks = []
    for j in range(8):
        for c in range(PIECES):
            lo = size * c // PIECES
            hi = size * (c + 1) // PIECES
            if hi > lo:
                tasks.append((j, lo, hi))
    if n < 1000000 or not hasattr(os, "fork"):
        return 3 + sum(work(n, primes, zeros, *t) for t in tasks)
    pipes = []
    for t in tasks:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            c = work(n, primes, zeros, *t)
            os.write(w, str(c).encode())
            os._exit(0)
        os.close(w)
        pipes.append((pid, r))
    total = 3
    for pid, r in pipes:
        data = b""
        while True:
            d = os.read(r, 64)
            if not d:
                break
            data += d
        os.close(r)
        os.waitpid(pid, 0)
        total += int(data)
    return total


if __name__ == "__main__":
    print(count_primes(int(sys.argv[1])))
