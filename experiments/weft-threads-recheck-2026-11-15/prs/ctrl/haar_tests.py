import numpy as np, sys
from weft.runtime.plasm.identifiability_gate import *
rng=np.random.default_rng(20261113)
P,O=32,6
xd=rng.standard_normal((12,P)); xt=rng.standard_normal((8,P)); st=np.vstack([xd,xt])
_,_,vh=np.linalg.svd(st,full_matrices=True); N=vh[20:]; R=vh[:20]
def gate(delta,mode,seed=2026,ep=0,dd=-0.15):
    tail=float(np.linalg.norm(xt@delta))
    r=evaluate_haar_refreshed_mpdi_gate(observed_peripheral_probes=st,candidate_peripheral_delta=delta,delta_dominant=dd,static_tail_delta=tail,static_tail_scale=0.25,haar_scale=0.50,colony_seed=seed,epoch=ep,max_haar_rows=mode)
    return r.mpdi_receipt.mpdi_gate_commits
def mk(null_frac,norm=4.0):
    a=R.T@rng.standard_normal((20,O)); a/=np.linalg.norm(a)
    b=N.T@rng.standard_normal((12,O)); b/=np.linalg.norm(b)
    d=np.sqrt(1-null_frac)*a+np.sqrt(null_frac)*b
    return d*norm
# note: in-span delta moves static tail probe too -> tail_delta large. scale tail so tail delta small: use norm param
print('A) commit rate, 100 trials, by fraction of update energy in unobserved null space; norm 4, tail probe sees in-span part')
for nf in [0,0.001,0.01,0.05,0.2,0.375,1.0]:
    row=[]
    for mode in (None,4):
        c=sum(gate(mk(nf),mode,ep=i) for i in range(100)); row.append(c)
    print(f' null_frac={nf}: commits full={row[0]}/100 sub4={row[1]}/100')
print('B) generic random update (isotropic), norm 4, static tail delta forced 0 as reviewer did')
cf=cs=0
for i in range(100):
    d=rng.standard_normal((P,O)); d*=4/np.linalg.norm(d)
    for mode in (None,4):
        r=evaluate_haar_refreshed_mpdi_gate(observed_peripheral_probes=st,candidate_peripheral_delta=d,delta_dominant=-0.15,static_tail_delta=0.0,static_tail_scale=0.25,haar_scale=0.5,colony_seed=2026,epoch=i,max_haar_rows=mode).mpdi_receipt.mpdi_gate_commits
        if mode is None: cf+=r
        else: cs+=r
print(f' commits full={cf}/100 sub4={cs}/100; expected null energy fraction 12/32=0.375')
print('C) grinding: rank-1 null-space attack norm 4 + jitter, sub4 mode, count tries to commit; 30 independent attack directions')
tries=[]
for k in range(30):
    base=N[k%12][:,None]@rng.standard_normal((1,O)); base*=4/np.linalg.norm(base)
    n=0
    while True:
        n+=1
        d=base+1e-4*(N.T@rng.standard_normal((12,O)))
        if gate(d,4,seed=2026+k,ep=0,dd=-0.15): break
        if n>20000: n=None;break
    tries.append(n)
print(' tries to first commit:',tries,'median',np.median([t for t in tries if t]))
print('   full mode grinding cap 3000 tries:', sum(gate(base+1e-4*(N.T@rng.standard_normal((12,O))),None) for _ in range(3000)),'commits of 3000')
