import sys
M=1000000007
P=2*(M+1)
def fib(n):
    n%=P
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if bit=='1':a,b=d,(c+d)%M
        else:a,b=c,d
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
