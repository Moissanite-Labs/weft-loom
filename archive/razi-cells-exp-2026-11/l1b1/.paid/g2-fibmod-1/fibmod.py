import sys
M=1000000007
P=2*(M+1)
S=65536
def main():
    toks=sys.stdin.buffer.read().split()
    if not toks: return
    A=[0]*(S+1);A[1]=1
    for i in range(2,S+1):A[i]=(A[i-1]+A[i-2])%M
    # F(S), F(S+1)
    fs=A[S]; fs1=(A[S-1]+A[S])%M
    # advance by S: (F(a),F(a+1)) -> (F(a+S),F(a+S+1)) via F(m+n)=F(m)F(n+1)+F(m-1)F(n)
    H0=[];H1=[]
    a,b=0,1
    for _ in range(P//S+2):
        H0.append(a);H1.append(b)
        # F(a+S)=a*fs1+(b-a)*fs ; F(a+S+1)=F(a+1)F(S+1)+F(a)F(S)
        a,b=(a*fs1+(b-a)*fs)%M,(b*fs1+a*fs)%M
    memo={}
    out=[]
    for t in toks:
        r=memo.get(t)
        if r is None:
            n=int(t)%P
            h=n>>16;l=n&65535
            fa=H0[h]
            r=(fa*A[l+1]+(H1[h]-fa)*A[l])%M
            memo[t]=r
        out.append(r)
    sys.stdout.write("\n".join(map(str,out))+"\n")
main()
