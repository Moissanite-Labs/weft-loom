import importlib.util, math, os, sys
from pathlib import Path
def _weft():
    a = sys.argv
    w = a[a.index("--weft") + 1] if "--weft" in a and a.index("--weft") + 1 < len(a) else os.environ.get("WEFT_CHECKOUT")
    if not w:
        raise SystemExit("give the weft software checkout with --weft PATH or the WEFT_CHECKOUT environment variable")
    return Path(w)
spec = importlib.util.spec_from_file_location("inv", (_weft() / "weft" / "runtime" / "invariants" / "invariants.py").resolve()); inv = importlib.util.module_from_spec(spec); spec.loader.exec_module(inv)
print("list path, diff 1e160:", inv.verify_weight_update_safety_ex([0.0,0.0],[1e160,0.0],1e308,10.0,1.0))
print("masked (scaled) path same input, mask=[0,0]:", inv.verify_weight_update_safety_ex([0.0,0.0],[1e160,0.0],1e308,10.0,1.0,[0,0]))
print("f64 r just below dist 1-2^-40:", inv.verify_weight_update_safety_ex([0.0],[1.0],1-2**-40,10.0,1.0))
print("budget 1+2^-40 cost 1:", inv.verify_weight_update_safety_ex([0.0],[0.1],1.0,1+2**-40,1.0))
