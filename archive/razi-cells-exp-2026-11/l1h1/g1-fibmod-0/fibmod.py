import sys
M=1000000007
P=2000000016
def fib(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=a*(2*b-a)%M
        u=(a*a+b*b)%M
        if c=='1':
            a,b=u,(t+u)%M
        else:
            a,b=t,u
    return a
def main():
    d=sys.stdin.read().split()
    if not d:
        return
    ns=[int(x)%P for x in d]
    try:
        import numpy as np
    except ImportError:
        np=None
    if np is None or len(ns)<64:
        c={}
        o=[]
        for n in ns:
            r=c.get(n)
            if r is None:
                r=c[n]=fib(n)
            o.append(r)
    else:
        arr=np.array(ns,dtype=np.int64)
        a=np.zeros(len(ns),dtype=np.int64)
        b=np.ones(len(ns),dtype=np.int64)
        for bit in range(31,-1,-1):
            t=a*((2*b-a)%M)%M
            u=(a*a+b*b)%M
            m=((arr>>bit)&1).astype(bool)
            a=np.where(m,u,t)
            b=np.where(m,(t+u)%M,u)
        o=a.tolist()
    sys.stdout.write("\n".join(map(str,o))+"\n")
main()
