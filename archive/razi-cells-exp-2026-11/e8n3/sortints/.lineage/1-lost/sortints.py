import ctypes, os, sys

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_fastsort.so'))
_run = _lib.fastsort_stdio
_run.restype = ctypes.c_int

def main():
    if _run() != 0:
        sys.stdin.seek(0)
        data = sys.stdin.read().split()
        ints = [int(x) for x in data]
        ints.sort()
        sys.stdout.write('\n'.join(str(x) for x in ints) + ('\n' if ints else ''))

if __name__ == '__main__':
    main()
