import sys, numpy as np
def main():
    data = sys.stdin.buffer.read()
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    a.sort()
    out = '\n'.join(map(str, a.tolist()))
    if len(a): out += '\n'
    sys.stdout.write(out)
main()
