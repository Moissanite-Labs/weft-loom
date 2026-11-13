import sys
M=1000000007
def fib(n):
    a=0;b=1
    for i in range(n.bit_length()-1,-1,-1):
        t=a*(2*b-a)%M
        u=(a*a+b*b)%M
        if (n>>i)&1:
            a=u;b=(t+u)%M
        else:
            a=t;b=u
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
