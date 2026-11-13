import json
HEAD = '''import sys

_Z = b'0' * 256

def _masks(a):
    try:
        ab = a.encode('latin-1')[::-1]
    except UnicodeEncodeError:
        masks = {}
        bit = 1
        for ch in a:
            masks[ch] = masks.get(ch, 0) | bit
            bit <<= 1
        return masks
    return {chr(c): int(ab.translate(_Z[:c] + b'1' + _Z[c + 1:]), 2) for c in set(ab)}

def lcs(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return 0
    m = len(a)
    masks = _masks(a)
    if not masks.keys() >= set(b):
        b = ''.join([ch for ch in b if ch in masks])
    full = (1 << m) - 1
'''
TAIL = '''
def main():
    data = sys.stdin.read().split("\\n")
    a = data[0].rstrip("\\r") if len(data) > 0 else ""
    b = data[1].rstrip("\\r") if len(data) > 1 else ""
    print(lcs(a, b))

if __name__ == "__main__":
    main()
'''
A = '''    v = full
    for mk in map(masks.__getitem__, b):
        u = v & mk
        v = ((v + u) | (v - u)) & full
    return m - v.bit_count()
'''
def chunk(K, op):
    return f'''    v = full
    ms = list(map(masks.__getitem__, b))
    for i in range(0, len(ms), {K}):
        for mk in ms[i:i + {K}]:
            u = v & mk
            v = (v + u) | (v {op} u)
        v &= full
    return m - v.bit_count()
'''
D = '''    v = -1
    for mk in map(masks.__getitem__, b):
        u = v & mk
        v = (v + u) | (v - u)
    return (~v).bit_count()
'''
vs = [HEAD + x + TAIL for x in [A, chunk(64, '-'), chunk(64, '^'), D, chunk(250, '^')]]
json.dump(vs, open('vs.json', 'w'))
import shutil, subprocess
shutil.copy('lcs.py', 'lcs_orig.py')
for i, v in enumerate(vs):
    open('lcs.py', 'w').write(v)
    open(f'v{i}.py', 'w').write(v)
    r = subprocess.run(['python3', 'check.py'], capture_output=True, text=True)
    b = subprocess.run(['python3', 'bench.py'], capture_output=True, text=True)
    print(i, r.stdout.strip(), r.stderr.strip()[-300:], b.stdout.strip())
shutil.copy('lcs_orig.py', 'lcs.py')
