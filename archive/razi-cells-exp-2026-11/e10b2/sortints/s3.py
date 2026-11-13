import sys, numpy as np
def main():
    data = sys.stdin.buffer.read().split()
    a = np.array(data, dtype='S').astype(np.int64)
    a.sort()
    out = '\n'.join(map(str, a.tolist()))
    if len(a): out += '\n'
    sys.stdout.write(out)
main()
