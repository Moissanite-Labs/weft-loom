import sys
M=1000000007
def fib(n):
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        a,b=(d,(c+d)%M) if bit=='1' else (c,d)
    return a
if __name__=="__main__":
    print(fib(int(sys.argv[1])))
