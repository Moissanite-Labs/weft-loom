import os, sys
import numpy as np

def numpy_path():
    data = sys.stdin.buffer.read()
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    a.sort()
    sys.stdout.write('\n'.join(map(str, a.tolist())) + '\n')

def main():
    # Prefer the compiled C sorter when present and runnable (fds are inherited).
    d = os.path.dirname(os.path.abspath(__file__))
    for name in ('sortints_c', 'sc'):
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            try:
                sys.stdout.flush()
                os.execv(p, [p])
            except Exception:
                pass
    numpy_path()

main()
