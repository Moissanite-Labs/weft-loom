import json, re, math, collections, pathlib, os, sys
loom=str(pathlib.Path(__file__).resolve().parents[4])
_a=sys.argv[1:]
weft=_a[_a.index("--weft")+1] if "--weft" in _a and _a.index("--weft")+1 < len(_a) else os.environ.get("WEFT_CHECKOUT")
if not weft: raise SystemExit("skeptic_probe: give the weft software checkout with --weft PATH or the WEFT_CHECKOUT environment variable")
cert=json.load(open(f"{loom}/experiments/e13-geodesic-shunting-plasmid-2026-11-12/e13_certificates.json"))
print("CERT keys:", list(cert)[:20])
# find per-seed structure
def walk(d,p=""):
    if isinstance(d,dict):
        for k,v in d.items():
            if isinstance(v,(dict,list)): walk(v,p+"/"+k)
            else: print(p+"/"+k,"=",v)
    elif isinstance(d,list):
        print(p, f"list len={len(d)}", str(d)[:300])
walk(cert)
print("\n--- binomial ---")
for k,n in [(12,12),(11,12)]:
    p=sum(math.comb(n,i) for i in range(k,n+1))/2**n
    print(f">= {k}/{n} one-sided p={p:.6f} two-sided~{min(1,2*p):.6f}")
print("\n--- register ---")
reg=pathlib.Path(f"{weft}/docs/corpus/claims-register.md").read_text()
rows=[l for l in reg.splitlines() if re.match(r"\|\s*[RMLHG]\d+",l)]
print("rows",len(rows))
c=collections.Counter()
for r in rows:
    for s in ["VERIFIED","REPORTED","OPEN"]:
        if s in r: c[s]+=1; break
print(c)
for id_ in ["R4","R10","R1","R2","M12","L1","L7"]:
    for r in rows:
        if re.match(rf"\|\s*{id_}\s*\|",r): print(id_, r[:180])
print("\n--- current bodies vs R4/R10 ---")
import os
print("ledger:", os.listdir(f"{weft}/weft/runtime/ledger"))
harv=pathlib.Path(f"{weft}/weft/runtime/telemetry/harvester.py")
print("harvester exists", harv.exists())
if harv.exists():
    t=harv.read_text(); print("fetch_live" in t, "1762560000" in t)
gh=list(pathlib.Path(f"{weft}/weft/runtime").rglob("github_harvester.py"))
print("github_harvester:", gh)
if gh: print(gh[0].read_text()[:600])
print("\n--- corpus_audit ---")
ca=pathlib.Path(f"{loom}/scripts/corpus_audit.py").read_text()
m=re.search(r'""".{0,400}"""',ca,re.S); print(m.group(0)[:500] if m else ca[:500])
