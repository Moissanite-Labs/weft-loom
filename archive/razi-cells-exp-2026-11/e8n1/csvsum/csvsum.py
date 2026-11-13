import os, ctypes

lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_csvsum.so"))
lib.run_csvsum.argtypes = [ctypes.c_int]
lib.run_csvsum.restype = ctypes.c_int

if __name__ == '__main__':
    lib.run_csvsum(0)
