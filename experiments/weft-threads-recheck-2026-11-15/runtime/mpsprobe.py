import sys, json, os, torch
_a=sys.argv[1:]
_w=_a[_a.index('--weft')+1] if '--weft' in _a and _a.index('--weft')+1 < len(_a) else os.environ.get('WEFT_CHECKOUT')
if not _w: raise SystemExit('give the weft software checkout with --weft PATH or the WEFT_CHECKOUT environment variable')
sys.path.insert(0,os.path.join(_w,'weft/runtime/invariants'))
from invariants import verify_weight_update_safety_ex, load_conformance_vectors
v=load_conformance_vectors()
dec=lambda x: float(x) if isinstance(x,str) else x
for dev in ("cpu","mps"):
  for vec in v["weight_update_vectors"]:
    b=torch.tensor([dec(x) for x in vec["baseline"]],dtype=torch.float32,device=dev)
    c=torch.tensor([dec(x) for x in vec["candidate"]],dtype=torch.float32,device=dev)
    try:
        r=verify_weight_update_safety_ex(b,c,vec["r_invariant"],vec["budget"],vec["cost"],vec.get("locked_mask"))
    except Exception as e:
        r=("EXC",repr(e)[:100])
    ok = r[0]==vec["expected_accepted"] and r[-1]==vec["expected_reason"] if r[0]!="EXC" else False
    if not ok: print(dev, vec["name"], "got",r,"want",vec["expected_accepted"],vec["expected_reason"])
