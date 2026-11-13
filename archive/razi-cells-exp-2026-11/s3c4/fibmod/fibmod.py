import sys
M=1000000007
def c(A,B):
    a1,a0=A;b1,b0=B
    return ((a0*b0+a1*b1)%M,(a0*(b0+b1)+a1*b0)%M)
def main():
    ns=list(map(int,sys.stdin.read().split()))
    mx=max(ns) if ns else 0
    K=12;m=(1<<K)-1
    L=max(1,(mx.bit_length()+K-1)//K)
    T=[];base=(0,1)
    for j in range(L):
        t=[(1,0),base]
        for i in range(2,1<<K):t.append(c(t[-1],base))
        T.append(t)
        for _ in range(K):base=c(base,base)
    o=[]
    for n in ns:
        r=(1,0);j=0
        while n:
            i=n&m
            if i:
                a1,a0=r;b1,b0=T[j][i]
                r=((a0*b0+a1*b1)%M,(a0*(b0+b1)+a1*b0)%M)
            n>>=K;j+=1
        o.append(r[1])
    print("\n".join(map(str,o)))
main()
