import random, numpy as np
from fractions import Fraction as F
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
import importlib.util
import sys
import sys as _sys
if len(_sys.argv) < 2: raise SystemExit('usage: t182.py WORKTREE_PATH')
WT = _sys.argv[1]
sys.path.insert(0,WT+'/weft/runtime/plasm'); import causal_synaptic_gate as c
# 1 randomized agreement with scipy bipartite matching on valid inputs
random.seed(1); bad=0; N=2000
for t in range(N):
    nr=random.randint(1,6); nrec=random.randint(1,8)
    rec=[(i,random.random()<0.8) for i in range(nrec)]
    prim=[(random.randint(1,nr),random.randrange(nrec)) for _ in range(random.randint(0,8))]
    sec=[(random.randint(1,nr),random.randrange(nrec)) for _ in range(random.randint(0,8))]
    cons={k for k in range(1,nr+1) if random.random()<0.5}
    cert=c.route_causal_synaptic_flow(nr,rec,prim,sec,cons)
    intact={i for i,b in rec if b}
    edges=[(i,r) for i,(k,r) in enumerate(prim) if r in intact]+[(len(prim)+j,r) for j,(k,r) in enumerate(sec) if k in cons and r in intact]
    L=len(prim)+len(sec)
    if L==0 or not edges: m=0
    else:
        rows=[e[0] for e in edges];cols=[e[1] for e in edges]
        M=csr_matrix((np.ones(len(edges)),(rows,cols)),shape=(L,nrec))
        m=int((maximum_bipartite_matching(M,perm_type='column')>=0).sum())
    if m!=cert.max_flow or not cert.primal_dual_verified: bad+=1
print('random valid-input agreement with scipy matching: mismatches',bad,'of',N)
# 2 reviewer collision
r=c.route_causal_synaptic_flow(1,[(1,True),(2,True)],[(1,2),(1,2),(1,2)],[],set())
print('1-based collision:',r.max_flow,r.cut_capacity,r.primal_dual_verified,'(true matching size is 1)')
try: c.route_causal_synaptic_flow(1,[(0,True),(5,True)],[(1,5)],[],set())
except Exception as e: print('id 5 ->',type(e).__name__)
r=c.route_causal_synaptic_flow(1,[(0,True)],[],[(99,0)],{99}); print('out-of-range secondary rung admitted: flow',r.max_flow)
# 3 mitosis gate
for rr in (1,11,19):
    d=c.certify_two_channel_mitosis_farkas(F(1,20),F(rr),F(1,4)); print('r',rr,d['rs_invariant_eps_star'],d['certified_above_ceiling'])
print('eps* vs p at r=19,c=1/4 (ceiling 1/60=%.4f):'%(1/60))
for k in (1,2,4,5,6,10,19):
    p=F(k,20); d=c.certify_two_channel_mitosis_farkas(p,F(19),F(1,4)); print(' p=%s eps*=%.4f certified=%s'%(p,float(d['rs_invariant_eps_star']),d['certified_above_ceiling']))
try: c.certify_two_channel_mitosis_farkas(F(1,2),F(-1),F(1,4))
except Exception as e: print('r=-1 ->',type(e).__name__)
d=c.certify_two_channel_mitosis_farkas(F(1,2),F(-3),F(1,4)); print('r=-3 certified?',d['certified_above_ceiling'],d['rs_invariant_eps_star'])
# 4 single-channel spoof inequality on a fine grid incl. continuous
bad=[p for p in [F(i,2000) for i in range(100,2001)] if not (abs((19*p)/(18*p+1)-(11*p+F(1,4)*(1-p))/(10*p+1))/2 < F(1,60))]
print('single-channel spoof inequality violations on p in [1/20,1] grid(1901 pts):',len(bad))
# does pair of channels help? what does single-channel gap look like for r=19 vs honest r=1 (no drift)
