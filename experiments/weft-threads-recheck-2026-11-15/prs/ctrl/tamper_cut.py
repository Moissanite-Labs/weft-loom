import dataclasses as dc, numpy as np
from weft.runtime.plasm.synaptic_flow import *
from weft.runtime.plasm.synaptic_flow import min_cut_certificate_digest
rs=np.random.default_rng(0).random(20)
c=allocate_disjoint_synaptic_corridors(rs,plasmid_demands=[4,4,4,4,4],core_rows=4)
print(c.requires_mitosis,c.deficit,c.max_flow,verify_min_cut_mitosis_certificate(c))
def tam(name,**kw):
    d=dc.replace(c,**kw)
    d0=verify_min_cut_mitosis_certificate(d)
    d=dc.replace(d,sha256_digest=min_cut_certificate_digest(d))
    print(name,'unsealed:',d0.get('ok'),'resealed:',verify_min_cut_mitosis_certificate(d))
tam('max_flow-1',max_flow=c.max_flow-1)
tam('deficit=0',deficit=0,requires_mitosis=False)
tam('assign swap',assignments=tuple(reversed(c.assignments)) if hasattr(c.assignments,'__len__') else c.assignments)
print([f.name for f in dc.fields(c)])
ne=list(c.network_edges); u,v,cap=ne[5]; ne[5]=(u,v,cap+1)
tam('edge cap+1',network_edges=tuple(ne))
ne=list(c.network_edges); ne.pop(5)
tam('edge dropped',network_edges=tuple(ne))
a=[list(x) for x in c.assignments]; a[0][0]=a[1][0]
tam('duplicate row across waves',assignments=tuple(tuple(x) for x in a))
a=[list(x) for x in c.assignments]; a[0][0]=0  # a frozen core row
tam('assign a frozen core row',assignments=tuple(tuple(x) for x in a))
tam('demand shrink',plasmid_demands=(4,4,4,4,3),total_demand=19)
