import sys
import re


def main():
    data = sys.stdin.buffer.read()
    if not data.strip():
        return
    # Fast path: numpy int64 sorting when every token fits in int64.
    # Any token with 19+ digits (ignoring an optional sign) is not guaranteed
    # to fit, so fall back to arbitrary-precision Python ints.
    if re.search(rb'[0-9]{19,}', data) is None:
        try:
            import numpy as np
            a = np.fromstring(data, dtype=np.int64, sep=' ')
            a.sort()
            out = '\n'.join(map(str, a.tolist()))
            sys.stdout.buffer.write((out + '\n').encode())
            return
        except Exception:
            pass
    nums = list(map(int, data.split()))
    nums.sort()
    sys.stdout.buffer.write(('\n'.join(map(str, nums)) + '\n').encode())


main()
