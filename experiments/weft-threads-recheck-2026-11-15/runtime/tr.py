import struct, math, random, subprocess, sys, os, importlib.util
from pathlib import Path
def _weft():
    a = sys.argv
    w = a[a.index("--weft") + 1] if "--weft" in a and a.index("--weft") + 1 < len(a) else os.environ.get("WEFT_CHECKOUT")
    if not w:
        raise SystemExit("give the weft software checkout with --weft PATH or the WEFT_CHECKOUT environment variable")
    return Path(w)
spec = importlib.util.spec_from_file_location("inv", (_weft() / "weft" / "runtime" / "invariants" / "invariants.py").resolve()); inv = importlib.util.module_from_spec(spec); spec.loader.exec_module(inv)
bits=lambda x: struct.unpack("<I",struct.pack("<f",x))[0]
fb=lambda u: struct.unpack("<f",struct.pack("<I",u))[0]
INF=math.inf; nan=math.nan
ts=[nan,INF,-INF,0.0,-0.0,-1e-45,1e-45,14.999999,15.0,15.000001,34.999996,35.0,35.000004,84.99999,85.0,85.000008,100.0,-1.0,3.4028234e38]
ts=[fb(bits(x)) for x in ts]
rng=random.Random(5); ts += [fb(bits(rng.uniform(0,120))) for _ in range(300)]
ms=[fb(bits(x)) for x in [85.0,0.0,-1.0,nan,INF,-INF,100.0,15.0,35.0,1e-45]]
cases=[(t,m) for t in ts for m in ms]
open("t_in.txt","w").write("".join(f"{bits(t)} {bits(m)}\n" for t,m in cases))
gb=[0,1,2,6,10000,9999,10001,2**63,2**64-1,12297829382473034, 12297829382473035, 18446744073709551615//1500, 18446744073709551615//1500+1, 10**16, 10**17, 10**18, 10**19]+[rng.randrange(0,2**64) for _ in range(200)]+[rng.randrange(0,2**50) for _ in range(200)]
bp=[0,1,1500,5000,10000,10001,12345,2**32,2**63,2**64-1]
rc=[(g,b) for g in gb for b in bp]
open("r_in.txt","w").write("".join(f"{g} {b}\n" for g,b in rc))
out=subprocess.run(["./tr","t_in.txt","r_in.txt"],capture_output=True,text=True,check=True).stdout.split("\n")
tl=out[:len(cases)]; rl=[l for l in out if l.startswith("R ")]
dis=0; ex=[]
for (t,m),l in zip(cases,tl):
    a,h,e=map(int,l.split()); p=inv.verify_tension_bound(t,m)
    if (p["accepted"],p["homeostatic"],p["excision_triggered"])!=(bool(a),bool(h),bool(e)):
        dis+=1; ex.append((t,m,p,(a,h,e)))
print("tension cases",len(cases),"disagreements",dis)
for x in ex[:6]: print("  ",x)
# classify
import collections
c=collections.Counter()
for t,m,p,cc in ex: c[("py_acc",p["accepted"],"c_acc",bool(cc[0]),"py_reason",p["reason"])]+=1
print(dict(c))
dr=0; exr=[]; cnt=collections.Counter()
for (g,b),l in zip(rc,rl):
    _,u,w=l.split(); u=int(u); w=int(w)
    try: p=inv.compute_royalty_split(g,b); pu,pw=p["upstream_wei"],p["weaver_wei"]
    except ValueError as e: pu=pw="ValueError"
    if (pu,pw)!=(u,w):
        dr+=1; kind=("py ValueError" if pu=="ValueError" else ("u64 overflow of gross*bps" if g*b>=2**64 else "other"))
        cnt[kind]+=1
        if len(exr)<8 or kind=="other": exr.append((g,b,pu,pw,u,w,kind))
print("royalty cases",len(rc),"disagreements",dr,dict(cnt))
for x in exr[:8]: print("  ",x)
smallest=min((g for (g,b),l in zip(rc,rl) if b==1500 and (lambda pu,pw:(pu,pw))(*[inv.compute_royalty_split(g,b)[k] for k in("upstream_wei","weaver_wei")])!=tuple(map(int,l.split()[1:]))),default=None)
print("smallest gross in my set at bps=1500 where C != Python:",smallest, "(threshold floor(2^64/1500) =",2**64//1500,"wei =",2**64/1500/1e18,"ETH)")
