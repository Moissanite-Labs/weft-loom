import sys
M=1000000007
P=2*(M+1)
def main():
    out=[]
    ap=out.append
    for t in sys.stdin.buffer.read().split():
        n=int(t)%P
        a=0;b=1
        for c in bin(n)[2:]:
            d=a*(2*b-a)%M
            e=(a*a+b*b)%M
            if c=='1':
                a=e;b=(d+e)%M
            else:
                a=d;b=e
        ap(a)
    sys.stdout.write("\n".join(map(str,out))+"\n")
main()
