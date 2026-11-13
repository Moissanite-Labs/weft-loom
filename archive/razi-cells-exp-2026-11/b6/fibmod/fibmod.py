import sys
MOD=1000000007
def single(n):
    a,b=0,1
    for bit in bin(n%2000000016)[2:]:
        c=a*(2*b-a)%MOD; d=(a*a+b*b)%MOD
        a,b=(d,(c+d)%MOD) if bit=='1' else (c,d)
    return a
if __name__=='__main__':
    print(single(int(sys.argv[1])))
    sys.exit()
def add(a,b,c,d):
    x=a*c; y=b*d
    return (y-(b-a)*(d-c))%MOD,(x+y)%MOD
T0=[(0,1)]
for j in range(65535):
    a,b=T0[-1]; T0.append((b,(a+b)%MOD))
c,d=1,1
for j in range(16): c,d=add(c,d,c,d)
T1=[(0,1)]
for j in range(2000000015//65536): T1.append(add(*T1[-1],c,d))
def fib(n):
    n%=2000000016
    a,b=T0[n&65535]; c,d=T1[n>>16]
    return (b*d-(b-a)*(d-c))%MOD
