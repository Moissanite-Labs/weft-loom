import sys
import os
import ctypes

def _fallback():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    data.sort(key=int)
    sys.stdout.buffer.write(b"\n".join(data) + b"\n")

def main():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_sortints.so")
    if os.path.exists(so_path):
        try:
            lib = ctypes.CDLL(so_path)
            lib.fast_sort_fd.argtypes = [ctypes.c_int, ctypes.c_int]
            lib.fast_sort_fd.restype = ctypes.c_int
            sys.stdout.flush()
            res = lib.fast_sort_fd(0, 1)
            if res == 0:
                return
        except Exception:
            pass
    _fallback()

if __name__ == "__main__":
    main()
