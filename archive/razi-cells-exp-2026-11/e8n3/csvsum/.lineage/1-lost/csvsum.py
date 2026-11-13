import os, ctypes, subprocess

_dir = os.path.dirname(os.path.abspath(__file__))
_lib_path = os.path.join(_dir, "_csvsum.dylib")
if not os.path.exists(_lib_path):
    _c_path = os.path.join(_dir, "_csvsum.c")
    subprocess.run(["cc", "-O3", "-shared", "-fPIC", "-lpthread", _c_path, "-o", _lib_path], check=True)

_lib = ctypes.CDLL(_lib_path)
_lib.process_stdin.argtypes = []
_lib.process_stdin.restype = ctypes.c_int

if __name__ == "__main__":
    _lib.process_stdin()
