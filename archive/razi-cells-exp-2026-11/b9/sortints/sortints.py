import sys, os
import numpy as np
def main():
    data = os.read(0, 1<<30)
    while True:
        more = os.read(0, 1<<26)
        if not more: break
        data += more
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    if a.size:
        mn = int(a.min()); mx = int(a.max())
        if mn >= -2147483648 and mx <= 2147483647:
            a = a.astype(np.int32)
        a.sort()
        s = repr(a.tolist()).encode('ascii')
        b = s[1:-1].replace(b', ', b'\n') + b'\n'
        mv = memoryview(b)
        while mv:
            n = os.write(1, mv)
            mv = mv[n:]
main()
