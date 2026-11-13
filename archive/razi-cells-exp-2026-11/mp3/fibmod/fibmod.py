import sys
M=1000000007
P=2*(M+1)
def fd(n):
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if bit=='1':
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
def main():
    out=[]
    cache={}
    for l in sys.stdin.read().split():
        n=int(l)%P
        r=cache.get(n)
        if r is None:
            r=cache[n]=fd(n)
        out.append(r)
    sys.stdout.write("\n".join(map(str,out))+"\n")
main()
