import os, ctypes

lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_wf.so"))
lib.run_wf()
