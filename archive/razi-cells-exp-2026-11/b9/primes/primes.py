import sys
def count(n):
    if n < 3: return 0
    if n < 6: return 1 + (n > 3)
    # numbers 6k+1 (index k in a) and 6k+5 (index k in b); value v -> a: (v-1)//6 ; b: (v-5)//6
    la = (n - 2) // 6  # count of 6k+1 < n, k>=1 ... include k=0 (value 1) and mark it off
    la = (n - 1 + 5) // 6  # k such that 6k+1 < n -> k < (n-1)/6 -> k <= (n-2)//6 -> count (n-2)//6+1
    la = (n - 2) // 6 + 1
    lb = (n - 6) // 6 + 1 if n > 5 else 0
    a = bytearray([1]) * la
    b = bytearray([1]) * lb
    a[0] = 0
    r = int(n ** 0.5) + 1
    z = memoryview(bytes(max(la, lb) // 5 + 2))
    def mark(p):
        # mark multiples of p in class a (6k+1) and b (6k+5), starting at p*p
        pp = p * p
        # multiples of p that are 1 mod 6: p*m where m = 1 mod 6 if p = 1 mod 6, m = 5 mod 6 if p = 5 mod 6
        if p % 6 == 1:
            m1, m5 = pp, p * (p + 4)   # p*p = 1 mod 6 ; p*(p+4): (p+4) = 5 mod 6 -> product 5 mod 6
        else:
            m1, m5 = p * (p + 2), pp   # p = 5: (p+2) = 1 mod 6 -> product 5*1=5?? fix below
        # recompute cleanly: smallest multiple >= pp in each class
        c1 = pp if pp % 6 == 1 else pp + ((1 - pp) % 6) * 0
        # brute: step through m = p, p+... until residues found
        m = p
        f1 = f5 = 0
        while not (f1 and f5):
            v = p * m
            if v % 6 == 1 and not f1: f1 = v
            if v % 6 == 5 and not f5: f5 = v
            m += 1
        step = p
        if f1 < n:
            st = (f1 - 1) // 6
            a[st::step] = z[:len(range(st, la, step))]
        if f5 < n:
            st = (f5 - 5) // 6
            b[st::step] = z[:len(range(st, lb, step))]
    k = 0
    while True:
        p1 = 6 * k + 1
        p5 = 6 * k + 5
        if p1 > r and p5 > r: break
        if k < la and a[k] and p1 <= r and p1 > 1: mark(p1)
        if k < lb and b[k] and p5 <= r: mark(p5)
        k += 1
    return a.count(1) + b.count(1) + 2
print(count(int(sys.argv[1])))
