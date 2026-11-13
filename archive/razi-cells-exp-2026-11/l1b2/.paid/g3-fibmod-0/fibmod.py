import sys
def main():
    M=1000000007
    P=2*(M+1)
    S=65536
    F=[0,1]
    a,b=0,1
    for _ in range(S+1):
        a,b=b,(a+b)%M
        F.append(b)
    # F[i]=fib(i) for i up to S+2
    F=F[:S+3]
    s0,s1,sm=F[S],F[S+1],F[S-1]
    H=[]
    x,y=0,1  # fib(kS), fib(kS-1) at k=0: fib(-1)=1
    hn=(P>>16)+1
    HA=[0]*hn;HB=[0]*hn
    for k in range(hn):
        HA[k]=x;HB[k]=y
        x,y=(x*s1+y*s0)%M,(x*s0+y*sm)%M
    F1=F[1:S+1]
    F0=F[:S]
    data=sys.stdin.buffer.read().split()
    out=[]
    ap=out.append
    for t in data:
        n=int(t)%P
        h=n>>16;l=n&65535
        ap((HA[h]*F1[l]+HB[h]*F0[l])%M)
    if out:
        sys.stdout.write("\n".join(map(str,out))+"\n")
main()
