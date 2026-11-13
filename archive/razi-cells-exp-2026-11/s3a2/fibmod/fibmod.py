import sys
M=1000000007
N=2*(M+1)
def f(n):
    n%=N
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1:
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
def main():
    data=sys.stdin.read().split()
    c={}
    out=[]
    for s in data:
        r=c.get(s)
        if r is None:
            r=c[s]=f(int(s))
        out.append(r)
    sys.stdout.write("\n".join(map(str,out))+"\n")
main()
