import sys
from collections import defaultdict
def main():
    data = sys.stdin.buffer.read()
    t = data.replace(b'\n', b',').split(b',')
    if t and t[-1] == b'': t.pop()
    t = t[3:]
    d = defaultdict(float)
    for k, v in zip(t[1::3], map(float, t[2::3])):
        d[k] += v
    sys.stdout.write(''.join('%s,%.2f\n' % (k.decode(), v) for k, v in sorted(d.items())))
main()
