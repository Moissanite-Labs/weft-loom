import os, ctypes

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_maze.so"))
_lib.solve_stdin.restype = ctypes.c_int

if __name__ == "__main__":
    print(_lib.solve_stdin())
