import sys
def count(n, PRE=(5, 7, 11, 13)):
    if n < 3: return 0
    if n < 6: return 1 + (n > 3)
    la = (n - 2) // 6 + 1
    lb = (n - 6) // 6 + 1
    per = 1
    for p in PRE: per *= p
    pa = bytearray([1]) * per
    pb = bytearray([1]) * per
    for p in PRE:
        k0 = ((p * p - 1) // 6) % p
        pa[k0::p] = bytes(len(range(k0, per, p)))
        f5 = p * (p + 4) if p % 6 == 1 else p * (p + 2)
        k0 = ((f5 - 5) // 6) % p
        pb[k0::p] = bytes(len(range(k0, per, p)))
    reps = max(la, lb) // per + 1
    a = (pa * reps)[:la]
    b = (pb * reps)[:lb]
    a[0] = 0
    for p in PRE:
        if p < n:
            if p % 6 == 1: a[(p - 1) // 6] = 1
            else: b[(p - 5) // 6] = 1
    last = PRE[-1]
    r = int(n ** 0.5) + 1
    z = memoryview(bytes(max(la, lb) // 5 + 2))
    k = 0
    while True:
        p1 = 6 * k + 1
        p5 = 6 * k + 5
        if p1 > r: break
        if p1 > last and a[k]:
            st = (p1 * p1 - 1) // 6
            if st < la: a[st::p1] = z[:len(range(st, la, p1))]
            st = (p1 * (p1 + 4) - 5) // 6
            if st < lb: b[st::p1] = z[:len(range(st, lb, p1))]
        if p5 <= r and p5 > last and b[k]:
            st = (p5 * p5 - 1) // 6
            if st < la: a[st::p5] = z[:len(range(st, la, p5))]
            st = (p5 * (p5 + 2) - 5) // 6
            if st < lb: b[st::p5] = z[:len(range(st, lb, p5))]
        k += 1
    return a.count(1) + b.count(1) + 2
print(count(int(sys.argv[1])))
