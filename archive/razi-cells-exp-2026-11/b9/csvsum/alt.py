import sys
import numpy as np
def main():
    data=sys.stdin.buffer.read()
    h=data.index(b'\n')+1
    arr=np.frombuffer(data,dtype=np.uint8)[h:]
    if arr.size==0: return
    if arr[-1]!=10: arr=np.concatenate([arr,np.array([10],np.uint8)])
    nl=np.flatnonzero(arr==10)
    cm=np.flatnonzero(arr==44)
    c1=cm[0::2]; c2=cm[1::2]
    n=nl.size; last=arr.size-1
    cl=c2-c1-1; W=int(cl.max()); ar=np.arange(W)
    ci=np.minimum(c1[:,None]+1+ar,last)
    cb=np.where(ar<cl[:,None], arr[ci], 0).astype(np.uint8)
    cats=np.ascontiguousarray(cb).view('S%d'%W).ravel()
    uniq,inv=np.unique(cats,return_inverse=True)
    vl=nl-c2-1; L=int(vl.max()); ar=np.arange(L)
    vi=np.minimum(c2[:,None]+1+ar,last)
    vb=np.where(ar<vl[:,None], arr[vi], 32)
    neg=vb[:,0]==45
    isd=(vb>=48)&(vb<=57)
    dot=vb==46
    hasdot=dot.any(axis=1)
    dotcol=np.where(hasdot, dot.argmax(axis=1), L)
    fd=(isd & (ar[None,:]>dotcol[:,None])).sum(axis=1)
    m=np.zeros(n,np.int64)
    for j in range(L):
        d=isd[:,j]
        m=np.where(d, m*10+(vb[:,j]-48).astype(np.int64), m)
    m=np.where(neg,-m,m)
    F=int(fd.max())
    m=m*(10**(F-fd).astype(np.int64))
    tot=np.bincount(inv.ravel(),weights=m,minlength=uniq.size)
    out=[]
    for k,t in zip(uniq.tolist(),tot.tolist()):
        s=int(round(t))
        if F<=2:
            c=s*10**(2-F); a=abs(c)
            out.append('%s%s%d.%02d\n'%(k.decode(),'-' if c<0 else '',a//100,a%100))
        else:
            out.append('%s%.2f\n'%(k.decode(),s/10**F))
    sys.stdout.write(''.join(out))
main()
