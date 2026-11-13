import sys
M=1000000007
P=2*(M*M-1)
def f(n):
    a,b=0,1
    for ch in bin(n)[2:]:
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if ch=='1':
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
def main():
    cache={}
    out=[]
    ap=out.append
    for l in sys.stdin.buffer.read().split():
        n=int(l)%P
        r=cache.get(n)
        if r is None:
            r=cache[n]=f(n)
        ap(r)
    sys.stdout.write("\n".join(map(str,out))+"\n")
main()
