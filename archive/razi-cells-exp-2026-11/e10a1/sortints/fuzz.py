import io, random, cand, warnings
warnings.simplefilter('error')
random.seed(7)
def ref(data):
    try:
        a = sorted(map(int, data.split()))
    except ValueError:
        return 'ERR'
    return ('\n'.join(map(str, a)) + '\n').encode() if a else b''
def run(data):
    w = io.BytesIO()
    try:
        used = cand.fast(data, w)
        if not used:
            w = io.BytesIO(); cand.slow(data, w)
    except ValueError:
        return 'ERR', None
    return w.getvalue(), used
fixed = [b'', b'\n', b'  ', b'0', b'-0', b'007 -007 0', b'+5 3', b'1_000 2', b'-', b'1-2', b'1-2 -', b'--5', b'5-', b'- 5', b'1 -',
 b'9223372036854775807 1', b'-9223372036854775808 1', b'9223372036854775806 -9223372036854775806', b'99999999999999999999999 -99999999999999999999999 5',
 b'1\x0b2', b'1\x0c2', b'3\r\n2\r\n1', b'\t5\t4 ', b'abc', b'1.5', b'12 0x10', b'000000000000000000000000001 2', b'1e3']
bad = 0; nfast = 0
for d in fixed:
    g, used = run(d); nfast += bool(used)
    if g != ref(d): bad += 1; print('MISMATCH', d, g, ref(d))
wss = [' ', '\n', '\t', '\r\n', '  ']
for it in range(3000):
    k = random.randint(0, 40)
    toks = []
    for _ in range(k):
        e = random.choice([1, 2, 4, 5, 8, 9, 10, 13, 18, 19, 22])
        v = random.randint(-10**e, 10**e)
        s = str(v)
        p = random.random()
        if p < 0.03: s = s.replace('-', '-0') if v < 0 else '0' + s
        elif p < 0.04: s = '+' + s
        elif p < 0.045: s = s + '-'
        elif p < 0.05: s = '-' + s
        toks.append(s)
    d = ''.join(random.choice(wss) * random.randint(0, 1) if i == 0 else random.choice(wss) for i in range(1))
    d += ''.join(t + random.choice(wss) for t in toks)
    if random.random() < 0.3: d = d.rstrip()
    d = d.encode()
    g, used = run(d); nfast += bool(used)
    if g != ref(d):
        bad += 1
        if bad < 15: print('MISMATCH', d, g, ref(d))
print('bad', bad, 'fast used', nfast)
