import sys, numpy as np

def main():
    raw = sys.stdin.buffer.read()
    if not raw.strip():
        return
    arr = np.fromstring(raw, dtype=np.int64, sep=' ')
    arr.sort()
    sys.stdout.write('\n'.join(map(str, arr.tolist())) + '\n')

if __name__ == '__main__':
    main()
