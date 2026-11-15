import sys, importlib.util, numpy as np
import sys as _sys
if len(_sys.argv) < 2: raise SystemExit('usage: e11_ctrl.py WORKTREE_PATH')
WT = _sys.argv[1]
sys.path.insert(0,WT)
D=WT+'/docs/program/experiments/e11-plasmid-transfer-breaking-through-2026-11/run_e11.py'
spec=importlib.util.spec_from_file_location('e11',D); e=importlib.util.module_from_spec(spec); sys.modules['e11']=e; spec.loader.exec_module(e)
def one(seed, mode):
    tw,tb=e.task_hyperplanes(seed); xtr=e.sample_uniform(600,seed+10000); xj=e.sample_uniform(e.NJAC,seed+10001)
    mask=e.init_params(0).plastic_mask()
    pa=e.train_tasks(e.init_params(seed),mask,xtr,tw,tb,list(range(e.N_KEPT)),e.TRAIN_STEPS_KEPT); base=pa.clone()
    pa=e.train_tasks(pa,mask,xtr,tw,tb,[e.NEW_TASK],e.TRAIN_STEPS_NEW)
    if mode=='perm':
        pf=e.rng(seed+555).permutation(e.HIDDEN); pb=e.permute_params(base,pf)
    else:
        pb=e.train_tasks(e.init_params(seed+1000),mask,xtr,tw,tb,list(range(e.N_KEPT)),e.TRAIN_STEPS_KEPT)
    pre=pb.clone(); delta=e.params_delta(pa,base); dpl=e.plastic_vec_from_delta(delta,mask)
    h_a,_=e.forward(base,xj); h_b,_=e.forward(pb,xj)
    perm=pf if mode=='perm' else e.hungarian_permutation(h_a,h_b)
    J,U=e.jacobian_keep(pb,mask,xj)
    nd=e.project_null(dpl.copy(),J); ad=e.plastic_vec_from_delta(e.align_delta(delta,perm),mask); pd=e.project_null(ad.copy(),J)
    plas=e.rank1_probe_readout_correction(e.apply_plastic_delta(pb,mask,pd),pa,xj,e.NEW_TASK)
    arms={'zero(B unchanged)':pre,
      'null_only':e.apply_plastic_delta(pb,mask,nd),
      'plasmid':plas,
      'readout_only(no delta, A-probe fit)':e.rank1_probe_readout_correction(pre,pa,xj,e.NEW_TASK)}
    # supervised readout on true labels using A's training inputs (a fit; upper reference)
    h,_=e.forward(pb,xtr); y=e.labels_for(xtr,tw,tb,e.NEW_TASK); H=np.c_[h,np.ones(len(h))]
    w=np.linalg.lstsq(H,y,rcond=None)[0]; s=pre.clone(); s.w2[e.NEW_TASK]=w[:-1]; s.b2[e.NEW_TASK]=w[-1]; arms['supervised_linear_readout(true labels)']=s
    xn=e.sample_uniform(e.N_EVAL,seed+5000)
    out={}
    for k,p in arms.items():
        ret=e.eval_retention(pre,p,tw,tb,seed+7000)
        out[k]=(e.accuracy(p,xn,tw,tb,e.NEW_TASK),e.all_retention_probes_pass(ret))
    # structure of null space
    sv=np.linalg.svd(J,compute_uv=False); rank=int((sv>max(J.shape)*np.finfo(float).eps*sv.max()).sum())
    P=J.shape[1]; head=np.zeros(P,bool); 
    # plastic order: w1[4:,:] (96), b1[4:] (12), w2 (64) , b2 (4); head = w2[3,:], b2[3]
    off=96+12; idx=[off+3*16+i for i in range(16)]+[off+64+3]
    nullb=np.eye(P)-np.linalg.pinv(J)@J
    head_mask=np.zeros(P);head_mask[idx]=1
    # fraction of projector trace inside head coords
    frac=float(np.trace(nullb*np.diag(head_mask)))/max(np.trace(nullb),1e-12)
    return out,(P,rank,P-rank,frac,np.linalg.norm(nd)/np.linalg.norm(dpl))
for label,seeds in (('prereg seeds',[17,29,43,101,202]),('20 fresh seeds',list(range(1000,1020)))):
    for mode in ('cross','perm'):
        res=[one(s,mode) for s in seeds]
        print(f'== {label}, {mode}: new-task acc mean (and #seeds with all retention probes passing)')
        for k in res[0][0]:
            a=[r[0][k][0] for r in res]; rp=sum(r[0][k][1] for r in res)
            print(f'  {k:42s} acc={np.mean(a):.3f}  min={min(a):.3f} max={max(a):.3f}  retention-all-probes {rp}/{len(seeds)}')
        st=np.array([r[1] for r in res]); print(f'  J_keep: P={int(st[0,0])} rank mean={st[:,1].mean():.1f} nullity mean={st[:,2].mean():.1f}; fraction of null-projector trace on the new head coords (w2[3],b2[3])={st[:,3].mean():.3f}; ||null(delta)||/||delta|| mean={st[:,4].mean():.3f}')
