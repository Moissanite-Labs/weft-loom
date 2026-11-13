import sys
M=1000000007
def mul(x,y):
    a,b,c,d=x
    e,f,g,h=y
    return ((a*e+b*g)%M,(a*f+b*h)%M,(c*e+d*g)%M,(c*f+d*h)%M)
# T[k][v] = Q^(v*256^k), Q=[[1,1],[1,0]]; F(n) = entry [0][1] of Q^n
T=[]
B=(1,1,1,0)
for k in range(8):
    row=[(1,0,0,1)]
    for v in range(1,256):
        row.append(mul(row[-1],B))
    T.append(row)
    B=mul(row[-1],B)
def fib(n):
    r=(1,0,0,1)
    k=0
    while n:
        v=n&255
        if v:
            r=mul(r,T[k][v])
        n>>=8
        k+=1
    return r[1]
def main():
    data=sys.stdin.read().split()
    sys.stdout.write("\n".join(str(fib(int(x))) for x in data)+("\n" if data else ""))
main()
