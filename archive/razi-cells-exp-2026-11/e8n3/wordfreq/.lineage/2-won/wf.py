import ctypes
import os

_lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__) or ".", "_wf.dylib"))
_lib.run_wf()
