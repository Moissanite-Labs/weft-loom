import sys
import numpy as np
def main():
    data=sys.stdin.buffer.read()
    h=data.index(b'\n')+1
    flat=data[h:].replace(b'\n',b',').split(b',')
    if flat and flat[-1]==b'': flat.pop()
    cats=np.array(flat[1::3],dtype='S8').view(np.int64)
    vals=np.array(flat[2::3]).astype(np.float64)
    u,inv=np.unique(cats,return_inverse=True)
    tot=np.bincount(inv,weights=vals,minlength=len(u))
    ub=u.view('S8'); o=np.argsort(ub)
    sys.stdout.write(''.join('%s,%.2f\n'%(k.decode(),v) for k,v in zip(ub[o].tolist(),tot[o].tolist())))
main()
