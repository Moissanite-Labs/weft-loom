import os, sys
from numpy._core.multiarray import fromstring

def write_all(b):
    v = memoryview(b)
    while v:
        v = v[os.write(1, v):]

def main():
    raw = sys.stdin.buffer.read()
    if not raw:
        return
    arr = fromstring(raw, dtype='i8', sep=' ')
    n = len(arr)
    if n < 50000:
        arr.sort()
        write_all(('\n'.join(map(str, arr.tolist())) + '\n').encode())
        return
    k = 6
    arr.partition([(n * i) // k for i in range(1, k)])
    idx = k - 1
    child_pid = 0
    for i in range(k - 1, 0, -1):
        pid = os.fork()
        if pid != 0:
            idx = i
            child_pid = pid
            break
    else:
        idx = 0
    start = (n * idx) // k
    end = (n * (idx + 1)) // k
    sub = arr[start:end]
    sub.sort()
    b = ('\n'.join(map(str, sub.tolist())) + '\n').encode()
    if child_pid:
        os.waitpid(child_pid, 0)
    write_all(b)
    if idx < k - 1:
        os._exit(0)

if __name__ == '__main__':
    main()
