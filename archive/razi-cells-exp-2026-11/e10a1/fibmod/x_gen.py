import sys, time, random
P = 1000000007
def V(m):
    a, b = 2, 3
    for _ in range(m): a, b = b, (3*b - a) % P
    return a
TAIL = '''    if n & 1:
        r = a + b
    elif rev:
        r = 2 * a - 3 * b
    else:
        r = 2 * b - 3 * a
    return r * (600000004 if (q ^ rev) & 1 else 400000003) % 1000000007
if __name__ == "__main__":
    print(fib(int(sys.argv[1])))
'''
HEAD = '''import sys
def fib(n):
    q, k = divmod(n >> 1, 500000004)
    if k > 250000001:
        j = 500000003 - k
        rev = 1
    else:
        j = k
        rev = 0
'''
LOOP = '''            if bit == '1':
                a, b = (a * b - 3) % 1000000007, (b * b - 2) % 1000000007
            else:
                a, b = (a * a - 2) % 1000000007, (a * b - 3) % 1000000007
'''
c = {}
c['cur'] = open('fibmod.py').read()
c['h_loop'] = HEAD + '''    if j:
        a, b = 3, 7
        for bit in bin(j)[3:]:
''' + LOOP + '''    else:
        a, b = 2, 3
''' + TAIL
def tab(nb):
    T = tuple(V(m) for m in range(2**nb + 1))
    return HEAD + '''    if j < %d:
        a = T[j]
        b = T[j + 1]
    else:
        t = j >> (j.bit_length() - %d)
        a = T[t]
        b = T[t + 1]
        for bit in bin(j)[%d:]:
''' % (2**nb, nb, nb + 2) + LOOP + TAIL.replace('if __name__', 'T = %r\nif __name__' % (T,))
c['h_tab5'] = tab(5)
c['h_tab6'] = tab(6)
c['h_tab4'] = tab(4)
def unr(top, lazy):
    T = tuple(V(m) for m in range(2**top + 1))
    s = HEAD + '    t = j >> %d\n    a = T[t]\n    b = T[t + 1]\n' % (28 - top)
    for i, sh in enumerate(range(27 - top, -1, -1)):
        m = ' % 1000000007' if (not lazy or i % 2 == 1) else ''
        s += '''    if j & %d:
        a, b = (a * b - 3)%s, (b * b - 2)%s
    else:
        a, b = (a * a - 2)%s, (a * b - 3)%s
''' % (1 << sh, m, m, m, m)
    return s + TAIL.replace('if __name__', 'T = %r\nif __name__' % (T,))
c['unr2'] = unr(2, 0)
c['unr5'] = unr(5, 0)
c['unr5lazy'] = unr(5, 1)
ns = {}
ref = None
rnd = random.Random(7)
tests = list(range(300)) + [10**18, 10**18-1] + [rnd.randrange(10**18) for _ in range(3000)] + [rnd.randrange(4*10**9+100) for _ in range(3000)]
work = [rnd.randrange(10**17, 10**18) for _ in range(4000)]
fs = {}
for name, src in c.items():
    open('x_%s.py' % name, 'w').write(src)
    best = 1e9
    for _ in range(20):
        t = time.perf_counter(); code = compile(src, name, 'exec'); d = {'__name__': 'm'}; exec(code, d); best = min(best, time.perf_counter() - t)
    fs[name] = d['fib']
    res = [d['fib'](n) for n in tests]
    if ref is None: ref = res
    print(name, 'OK' if res == ref else 'WRONG', 'compile_us=%.0f' % (best * 1e6))
bt = {k: 1e9 for k in fs}
for _ in range(15):
    for k, f in fs.items():
        t = time.perf_counter()
        for n in work: f(n)
        bt[k] = min(bt[k], time.perf_counter() - t)
for k in bt: print(k, 'us/call=%.3f' % (bt[k] / len(work) * 1e6))
