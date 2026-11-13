import sys
M=1000000007
P=2*(M+1)
def fib(n):
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*(2*b-a)%M
        d=(a*a+b*b)%M
        if bit=='1':
            a,b=d,(c+d)%M
        else:
            a,b=c,d
    return a
out=[]
for x in sys.stdin.read().split():
    out.append(fib(int(x)%P))
print("\n".join(map(str,out)))
