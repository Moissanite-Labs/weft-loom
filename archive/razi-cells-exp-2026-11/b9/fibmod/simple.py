import sys
M=1000000007
def fib(n):
    a=0;b=1
    for bit in bin(n)[2:]:
        c=a*(2*b-a);d=(a*a+b*b)%M
        if bit=='1':a=d;b=(c+d)%M
        else:a=c%M;b=d
    return a
sys.stdout.write(str(fib(int(sys.argv[1])))+"\n")
