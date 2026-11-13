import sys
M=1_000_000_007
P=2*(M+1)
W=11;S=1<<W;K=S-1
def mul(x,y):
    a,b,c,d=x;e,f,g,h=y
    return ((a*e+b*g)%M,(a*f+b*h)%M,(c*e+d*g)%M,(c*f+d*h)%M)
def build():
    base=(1,1,1,0);T=[]
    for _ in range(3):
        row=[(1,0,0,1)]
        for _d in range(S-1):row.append(mul(row[-1],base))
        T.append(row);base=mul(row[-1],base)
    return T
T0,T1,T2=build()
def main():
    out=[];cache={}
    for s in sys.stdin.read().split():
        n=int(s)%P
        a,b,c,d=T0[n&K];e,f,g,h=T1[(n>>W)&K]
        x=(a*e+b*g)%M;y=(a*f+b*h)%M
        _,_,g2,h2=0,0,*T2[n>>(2*W)][2:]
        # need top-right of (x y; ..)*T2: x*f2+y*h2
        t=T2[n>>(2*W)]
        out.append((x*t[1]+y*t[3])%M)
    sys.stdout.write("\n".join(map(str,out))+"\n")
main()
