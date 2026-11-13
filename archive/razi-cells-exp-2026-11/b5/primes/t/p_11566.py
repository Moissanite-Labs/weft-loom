import sys
def count_primes(n, Q=(7,11,13)):
    if n < 31:
        return len([p for p in (2,3,5,7,11,13,17,19,23,29) if p < n])
    R = (1,7,11,13,17,19,23,29)
    inv = {r: pow(r, -1, 30) for r in R}
    sizes = [len(range(r, n, 30)) for r in R]
    L = 1
    for q in Q: L *= q
    C = []
    for j, rj in enumerate(R):
        sz = sizes[j]
        pat = bytearray([1])*L
        for q in Q:
            s = (-rj * pow(30, -1, q)) % q
            pat[s::q] = bytes(len(range(s, L, q)))
        c = pat*(sz//L + 1)
        del c[sz:]
        C.append(c)
    C[0][0] = 0
    for j in range(1, len(Q)+1): C[j][0] = 1
    qmax = Q[-1]
    OFF = []
    for ri in R:
        lst = []
        for j, rj in enumerate(R):
            off = ((rj*inv[ri]) % 30 - ri) % 30
            lst.append((C[j], sizes[j], off, rj))
        OFF.append(lst)
    r = int(n**0.5)
    z = memoryview(bytes(sizes[0]//7 + 2))
    k = 0
    done = False
    while not done:
        base = 30*k
        for i in range(8):
            p = base + R[i]
            if p > r:
                done = True; break
            if p <= qmax or not C[i][k]: continue
            pp = p*p
            for Cj, sz, off, rj in OFF[i]:
                s = (pp + p*off - rj)//30
                Cj[s::p] = z[:len(range(s, sz, p))]
        k += 1
    return sum(c.count(1) for c in C) + 3
if __name__ == '__main__':
    print(count_primes(int(sys.argv[1])))
