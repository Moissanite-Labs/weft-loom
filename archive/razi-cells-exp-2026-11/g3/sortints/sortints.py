import sys


def main():
    import numpy as np
    data = sys.stdin.buffer.read()
    nums = np.fromstring(data.decode(), dtype=np.int64, sep=' ')
    nums.sort()
    out = '\n'.join(map(str, nums.tolist()))
    sys.stdout.buffer.write((out + '\n').encode())


main()
