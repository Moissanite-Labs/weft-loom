import sys
def main():
    data = sys.stdin.buffer.read()
    try:
        import numpy as np
        a = np.fromstring(data, dtype=np.int64, sep=' ')
        a.sort(kind='stable')
        nums = a.tolist()
    except Exception:
        nums = sorted(map(int, data.split()))
    w = sys.stdout.buffer.write
    w("\n".join(map(str, nums)).encode())
    w(b"\n")
main()
