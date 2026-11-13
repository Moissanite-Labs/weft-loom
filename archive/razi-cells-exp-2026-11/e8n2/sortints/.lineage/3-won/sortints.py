import os, sys

def main():
    so_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_fastsort.so")
    if os.path.exists(so_path):
        try:
            import ctypes
            lib = ctypes.CDLL(so_path)
            if lib.sort_fd0_to_fd1() == 0:
                return
        except Exception:
            pass
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    data.sort(key=int)
    sys.stdout.buffer.write(b'\n'.join(data) + b'\n')

if __name__ == '__main__':
    main()
