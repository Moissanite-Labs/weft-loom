import sys
def count_primes(n):
    if n < 31:
        return len([p for p in (2,3,5,7,11,13,17,19,23,29) if p < n])
    R = (1,7,11,13,17,19,23,29)
    inv = {r: pow(r, -1, 30) for r in R}
    T = [[(rj*inv[ri]) % 30 for rj in R] for ri in R]
    sizes = [len(range(r, n, 30)) for r in R]
    C = [bytearray([1])*s for s in sizes]
    C[0][0] = 0
    r = int(n**0.5)
    z = memoryview(bytes(sizes[0]//7 + 2))
    k = 0
    done = False
    while not done:
        base = 30*k
        for i in range(8):
            v = base + R[i]
            if v > r:
                done = True; break
            if v < 7 or not C[i][k]: continue
            p = v
            Ti = T[i]
            for j in range(8):
                rj = R[j]
                m0 = p + ((Ti[j] - R[i]) % 30)
                s = (p*m0 - rj)//30
                sz = sizes[j]
                Cj = C[j]
                Cj[s::p] = z[:len(range(s, sz, p))]
        k += 1
    return sum(c.count(1) for c in C) + 3
print(count_primes(int(sys.argv[1])))
