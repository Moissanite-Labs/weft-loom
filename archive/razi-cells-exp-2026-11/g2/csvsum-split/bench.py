import subprocess, sys, time

EXPECTED = open('expected.txt','rb').read()
DATA = open('data.csv','rb').read()

CAND = {}

CAND['float_csv'] = '''import sys, csv
NL = chr(10)
def main():
    r = csv.reader(sys.stdin)
    next(r, None)
    sums = {}
    for row in r:
        if len(row) < 3:
            continue
        try:
            v = float(row[2])
        except ValueError:
            continue
        c = row[1]
        sums[c] = sums.get(c, 0.0) + v
    out = []
    for c in sorted(sums):
        out.append('%s,%.2f' % (c, sums[c]))
    sys.stdout.write(NL.join(out) + NL)
main()
'''

CAND['float_split'] = '''import sys
NL = chr(10)
def main():
    inp = sys.stdin
    next(inp, None)
    sums = {}
    for line in inp:
        p = line.split(',')
        if len(p) < 3:
            continue
        try:
            v = float(p[2])
        except ValueError:
            continue
        c = p[1]
        sums[c] = sums.get(c, 0.0) + v
    out = []
    for c in sorted(sums):
        out.append('%s,%.2f' % (c, sums[c]))
    sys.stdout.write(NL.join(out) + NL)
main()
'''

CAND['cents_split'] = '''import sys
NL = chr(10)
def main():
    inp = sys.stdin
    next(inp, None)
    sums = {}
    for line in inp:
        p = line.split(',')
        if len(p) < 3:
            continue
        s = p[2].strip()
        neg = s[:1] == '-'
        if neg:
            s = s[1:]
        if '.' in s:
            w, fr = s.split('.', 1)
            fr = (fr + '00')[:2]
        else:
            w, fr = s, '00'
        try:
            v = int(w) * 100 + int(fr)
        except ValueError:
            continue
        if neg:
            v = -v
        c = p[1]
        sums[c] = sums.get(c, 0) + v
    out = []
    for c in sorted(sums):
        t = sums[c]
        sign = '-' if t < 0 else ''
        t = abs(t)
        out.append('%s,%s%d.%02d' % (c, sign, t // 100, t % 100))
    sys.stdout.write(NL.join(out) + NL)
main()
'''

def bench(name, code):
    fn = 'cand_' + name + '.py'
    open(fn, 'w').write(code)
    best = None
    ok = False
    for _ in range(2):
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, fn], input=DATA, capture_output=True)
        dt = time.perf_counter() - t0
        if r.stdout == EXPECTED:
            ok = True
        if best is None or dt < best:
            best = dt
    return ok, best

results = {}
for name in CAND:
    ok, dt = bench(name, CAND[name])
    fit = (1.0 / dt) if ok else 0.0
    results[name] = (ok, dt, fit)
    print(name, 'ok' if ok else 'WRONG', '%.3fs' % dt, 'fit=%.4f' % fit)

correct = [n for n in results if results[n][0]]
best_name = max(correct, key=lambda n: results[n][2]) if correct else None
print('BEST', best_name)
if best_name:
    open('csvsum.py', 'w').write(CAND[best_name])
    print('wrote csvsum.py from', best_name)
