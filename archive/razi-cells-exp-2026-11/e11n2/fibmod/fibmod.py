import sys
M=1000000007
def fib(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=a*((2*b-a)%M)%M
        u=(a*a+b*b)%M
        a,b=(u,(t+u)%M) if c=='1' else (t,u)
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
