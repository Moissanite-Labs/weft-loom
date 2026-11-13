import sys
M=1000000007
def fib(n):
    a,b=0,1
    for c in bin(n)[2:]:
        a,b=a*(2*b-a)%M,(a*a+b*b)%M
        if c=='1': a,b=b,(a+b)%M
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
