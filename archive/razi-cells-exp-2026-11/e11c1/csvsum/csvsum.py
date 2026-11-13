import sys
from collections import defaultdict
def main():
    t = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    d = defaultdict(float)
    for k, v in zip(t[4::3], map(float, t[5::3])):
        d[k] += v
    for k in sorted(d):
        print("%s %.2f" % (k.decode(), d[k]))
main()
