import sys
M=1000000007
P=2*(M+1)
def comb(x,y):
    a,c=x;b,d=y
    ab=a*b
    return ((a*d+c*b-ab)%M,(c*d+ab)%M)
def fd(n):
    a,b=0,1
    for ch in bin(n)[2:]:
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if ch=='1': a,b=d,(c+d)%M
        else: a,b=c,d
    return a,b
T=[]
for j in range(3):
    s=fd(1<<(11*j));t=[(0,1)]
    for k in range(2047): t.append(comb(t[-1],s))
    T.append(t)
T0,T1,T2=T
def main():
    out=[]
    for l in sys.stdin.read().split():
        n=int(l)%P
        a,c=T0[n&2047];b,d=T1[(n>>11)&2047]
        ab=a*b
        a,c=(a*d+c*b-ab)%M,(c*d+ab)%M
        b,d=T2[n>>22]
        out.append((a*d+c*b-a*b)%M)
    print("\n".join(map(str,out)))
main()
