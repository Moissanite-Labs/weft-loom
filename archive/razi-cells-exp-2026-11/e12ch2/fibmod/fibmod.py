import sys
M=1000000007
def fib(n):
    a,b=0,1
    for c in bin(n)[2:]:
        t=a*(2*b-a)
        u=a*a+b*b
        if c=='1':a,b=u%M,(t+u)%M
        else:a,b=t%M,u%M
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
