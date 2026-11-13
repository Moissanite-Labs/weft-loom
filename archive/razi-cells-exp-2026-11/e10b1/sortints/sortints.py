import sys


def _pure(data):
    a = [int(x) for x in data.split()]
    a.sort()
    return a


def main():
    data = sys.stdin.buffer.read()
    out = sys.stdout.buffer
    a = None
    try:
        import warnings
        import numpy as np
        with warnings.catch_warnings():
            # malformed input makes fromstring warn; turn that into a fallback
            warnings.simplefilter('error')
            arr = np.fromstring(data, dtype=np.int64, sep=' ')
        n = len(arr)
        if n:
            lo = int(arr.min())
            hi = int(arr.max())
            # possible int64 overflow/clamping: let the exact path decide
            if lo <= -(2 ** 62) or hi >= 2 ** 62:
                raise OverflowError
            if lo >= -(2 ** 31) and hi < 2 ** 31:
                arr = arr.astype(np.int32)
            arr.sort()
        a = arr.tolist()
    except Exception:
        a = _pure(data)
    if a:
        out.write(('%d\n' * len(a) % tuple(a)).encode('ascii'))
    out.flush()


if __name__ == '__main__':
    main()
