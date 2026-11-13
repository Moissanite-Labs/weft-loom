import sys
def main():
    M=1000000007
    P=2*(M+1)
    data=sys.stdin.buffer.read().split()
    # tables: 3 limbs of 11 bits
    B=11; S=1<<B; mask=S-1
    tabs=[]
    # base pair for step x=2^(11k): (F(x),F(x+1))
    def mul(a,b):
        fa,ga=a; fb,gb=b
        return ((fa*gb+(ga-fa)*fb)%M,(ga*gb+fa*fb)%M)
    step=(0,1); one=(1,1)
    # step for limb 0: x=1 -> (1,1)
    st=(1,1)
    for k in range(3):
        t=[(0,1)]
        cur=(0,1)
        for v in range(1,S):
            cur=mul(cur,st)
            t.append(cur)
        tabs.append(t)
        st=mul(t[S-1],st)
    t0,t1,t2=tabs
    cache={}
    out=[]
    for tok in data:
        r=cache.get(tok)
        if r is None:
            n=int(tok)%P
            fa,ga=t2[n>>22]
            fb,gb=t1[(n>>11)&mask]
            fa,ga=(fa*gb+(ga-fa)*fb)%M,(ga*gb+fa*fb)%M
            fb,gb=t0[n&mask]
            r=str((fa*gb+(ga-fa)*fb)%M)
            cache[tok]=r
        out.append(r)
    sys.stdout.write("\n".join(out)+("\n" if out else ""))
main()
