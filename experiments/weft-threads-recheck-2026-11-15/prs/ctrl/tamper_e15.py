import json,hashlib,copy,sys,importlib.util,subprocess
import sys as _sys
if len(_sys.argv) < 2: raise SystemExit('usage: tamper_e15.py WORKTREE_PATH')
WT = _sys.argv[1]
spec=importlib.util.spec_from_file_location('v',WT+'/papers/03-certified-morphogenesis/verify_e15.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
rep=json.load(open(WT+'/papers/03-certified-morphogenesis/e15_certificate.json'))
def seal(r):
    b={k:x for k,x in r.items() if k!='certificate_sha256'}
    r['certificate_sha256']=hashlib.sha256(json.dumps(b,sort_keys=True,separators=(',',':')).encode()).hexdigest();return r
print('original',v.verify_e15_dict(rep))
def t(name,fn,reseal):
    r=copy.deepcopy(rep);fn(r)
    if reseal: seal(r)
    print(name,'reseal' if reseal else 'noreseal','->',v.verify_e15_dict(r))
t('M3 mean_r2 -> -5',lambda r:r['summary_by_regime']['M3_full_dual_morphogenesis'].__setitem__('mean_shifted_ood_r2',-5.0),False)
t('M3 mean_r2 -> -5',lambda r:r['summary_by_regime']['M3_full_dual_morphogenesis'].__setitem__('mean_shifted_ood_r2',-5.0),True)
def m3wave(r):
    for s in r['per_seed_records']:
        s['regimes']['M3_full_dual_morphogenesis']['wave_r2s']=[-9.0]*5; s['regimes']['M3_full_dual_morphogenesis']['mean_shifted_ood_r2']=-9.0
t('M3 per-seed wave r2 all -9 (passed flag kept True)',m3wave,True)
def m0(r):
    for s in r['per_seed_records']:
        s['regimes']['M0_fixed_scalar']['passed_joint_gate']=True
    r['summary_by_regime']['M0_fixed_scalar']['passes_of_12']=12
t('M0 claims 12/12 pass',m0,True)
def poison(r):
    for s in r['per_seed_records']:
        x=s['regimes']['M3_full_dual_morphogenesis'];x['poison_committed']=2;x['poison_vetoed']=0
t('M3 poison committed=2 per seed (summary untouched)',poison,True)
def poison2(r):
    for s in r['per_seed_records']:
        x=s['regimes']['M3_full_dual_morphogenesis'];x['poison_committed']=2;x['poison_vetoed']=10
t('M3 poison_committed=2, vetoed kept 10',poison2,True)
