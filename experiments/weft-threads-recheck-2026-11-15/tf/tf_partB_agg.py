"""Aggregate step5, step5b, step6 outputs into partB_summary.out/json. Success = reverse >= 0.99 and COPY, ADD3 >= 0.98 (graft arms)."""
import glob, json
import numpy as np
from tf_common import clopper_pearson, die
def ok(e): return e['3'] >= 0.99 and e['0'] >= 0.98 and e['1'] >= 0.98
rows = [json.load(open(f))[0] for f in sorted(glob.glob('step6_main_s*.json'))]
rows.sort(key=lambda r: r['seed'])
n = len(rows)
if n < 6: die("fewer than 6 seeds")
out = {"seeds": [r['seed'] for r in rows], "variants": {}, "controls": {}}
print("graft variants (n=%d seeds, success: rev>=0.99 and natives>=0.98, fresh-draw set)" % n)
for v in rows[0]['variants']:
    k = sum(ok(r['variants'][v]['external']['in']) for r in rows)
    lo, hi = clopper_pearson(k, n)
    kh = sum(ok(r['variants'][v]['external']['ho']) for r in rows)
    revs = [r['variants'][v]['external']['in']['3'] for r in rows]
    nat = np.mean([min(r['variants'][v]['external']['in']['0'], r['variants'][v]['external']['in']['1']) for r in rows])
    fro = [r['variants'][v].get('frob_dist') for r in rows]
    print(f"{v:8s} success {k}/{n} CP95 [{lo:.2f},{hi:.2f}] heldout-set {kh}/{n}; rev per seed {revs}; mean min-native {nat:.4f}; bytes {rows[0]['variants'][v]['graft_bytes_fp16']}; frob {None if fro[0] is None else [round(x,1) for x in fro]}")
    out["variants"][v] = dict(success=k, n=n, cp95=[lo, hi], heldout_success=kh, rev=revs)
any_ok = [r['seed'] for r in rows if any(ok(r['variants'][v]['external']['in']) for v in r['variants'])]
print("seeds where at least one variant succeeds:", any_ok)
print("\ncontrols")
names = {}
for f in sorted(glob.glob('step6_ctl*_s*.json')):
    r = json.load(open(f))[0]
    for v, d in r['variants'].items():
        names.setdefault(v, {})[r['seed']] = d
for v, d in sorted(names.items()):
    print(v, {s: (x['external']['in']['0'], x['external']['in']['1'], x['external']['in']['3']) for s, x in sorted(d.items())})
    out["controls"][v] = {s: x['external']['in'] for s, x in d.items()}
json.dump(out, open('partB_summary.json', 'w'), indent=1)
