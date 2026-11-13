import ctypes, os
lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__) or ".", "_wf.dylib"))
lib.run_wf()
