import sys
M=1000000007
def fib(n):
    a,b=0,1
    for c in bin(n)[2:]:
        d=a*(2*b-a)%M
        e=(a*a+b*b)%M
        if c=='1':a,b=e,(d+e)%M
        else:a,b=d,e
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
