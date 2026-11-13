import sys
M=1000000007
def f(n):
    a,b=0,1
    for i in range(n.bit_length()-1,-1,-1):
        c=a*((2*b-a)%M)%M
        d=(a*a+b*b)%M
        if n>>i&1: a,b=d,(c+d)%M
        else: a,b=c,d
    return a
if __name__=="__main__":
    print(f(int(sys.argv[1])))
