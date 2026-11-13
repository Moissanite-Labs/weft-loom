import sys
M=1000000007
def fib(n):
    n%=2000000016
    a,b=0,1
    for c in bin(n)[3:]:
        d=a*(2*b-a)%M
        e=(a*a+b*b)%M
        if c=='1':
            a,b=e,d+e
            if b>=M:b-=M
        else:
            a,b=d,e
    return a if n else 0
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
