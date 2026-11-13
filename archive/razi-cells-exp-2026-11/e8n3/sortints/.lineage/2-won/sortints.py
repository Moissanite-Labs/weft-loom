import os
import ctypes

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_fastsort.so'))
_sort = _lib.sort_stdin_stdout
_sort.argtypes = []
_sort.restype = ctypes.c_int

if __name__ == '__main__':
    if _sort() != 0:
        import sys
        data = sys.stdin.read().split()
        ints = [int(x) for x in data]
        ints.sort()
        sys.stdout.write('\n'.join(str(x) for x in ints) + ('\n' if ints else ''))
