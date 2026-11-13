import sys, os
os.environ.setdefault('KMP_WARNINGS', '0')

def slow(data, w):
    a = list(map(int, data.split()))
    a.sort()
    if a:
        w.write(('\n'.join(map(str, a)) + '\n').encode())

def fast(data, w):
    if not data or data.isspace():
        return True
    if data.translate(None, b'0123456789- \n\t\r'):
        return False
    import numpy as np
    if b'-' in data:
        arr = np.frombuffer(data, dtype=np.uint8)
        mp = np.flatnonzero(arr == 45)
        if mp[-1] == len(data) - 1 or (arr[mp + 1] < 48).any():
            return False
        if mp[0] == 0:
            mp = mp[1:]
        if (arr[mp - 1] > 32).any():
            return False
    a = np.fromstring(data.decode('ascii'), dtype=np.int64, sep=' ')
    n = a.size
    if n == 0:
        return not data.strip()
    a.sort()
    if a[0] <= -9223372036854775807 or a[-1] >= 9223372036854775807:
        return False
    r = np.arange(10000)
    T = np.empty((10000, 4), np.uint8)
    T[:, 3] = r % 10 + 48
    T[:, 2] = r // 10 % 10 + 48
    T[:, 1] = r // 100 % 10 + 48
    T[:, 0] = r // 1000 + 48
    P = [10 ** d for d in range(1, 19)]
    k0 = int(np.searchsorted(a, 0))
    groups = []
    total = 0
    if k0:
        neg = a[:k0]
        b = [k0] + np.searchsorted(neg, [-p for p in P], side='right').tolist() + [0]
        for d in range(19, 0, -1):
            lo, hi = b[d], b[d - 1]
            if hi > lo:
                groups.append((lo, hi, d, 1))
                total += (hi - lo) * (d + 2)
    if k0 < n:
        b = [0] + np.searchsorted(a[k0:], P, side='left').tolist() + [n - k0]
        for d in range(1, 20):
            lo, hi = b[d - 1], b[d]
            if hi > lo:
                groups.append((k0 + lo, k0 + hi, d, 0))
                total += (hi - lo) * (d + 1)
    buf = np.empty(total, np.uint8)
    off = 0
    for lo, hi, d, sign in groups:
        u = a[lo:hi]
        if sign:
            u = -u
        m = hi - lo
        wd = d + sign + 1
        out = buf[off:off + m * wd].reshape(m, wd)
        off += m * wd
        col = wd - 1
        out[:, col] = 10
        if sign:
            out[:, 0] = 45
        rem = d
        if rem <= 9:
            u = u.astype(np.uint32)
        while rem > 4:
            q = u // 10000
            if rem > 9 and rem - 4 <= 9:
                q = q.astype(np.uint32)
                rr = (u - q * np.int64(10000)).astype(np.intp)
            else:
                rr = u - q * 10000
            out[:, col - 4:col] = T[rr]
            col -= 4
            rem -= 4
            u = q
        out[:, col - rem:col] = T[u, 4 - rem:]
    w.write(buf.data)
    return True

def main():
    data = sys.stdin.buffer.read()
    w = sys.stdout.buffer
    if not fast(data, w):
        slow(data, w)

if __name__ == '__main__':
    main()
