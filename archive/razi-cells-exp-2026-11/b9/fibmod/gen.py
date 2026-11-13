import sys
M=1000000007
W=int(sys.argv[1])
NW=(60+W-1)//W
# table[w][d] = (F(d<<(wW)), F(d<<(wW)+1)) mod M
def fibpair(n):
    a,b=0,1
    for bit in bin(n)[2:]:
        c=a*(2*b-a); d=(a*a+b*b)%M
        if bit=='1': a=d; b=(c+d)%M
        else: a=c%M; b=d
    return a,b
rows=[]
for w in range(NW):
    rows.append([fibpair(d<<(w*W)) for d in range(1<<W)])
out=[]
out.append("import sys\nM=1000000007\n")
out.append("T=("+",".join("("+",".join("(%d,%d)"%p for p in r)+")" for r in rows)+")\n")
out.append(f"""def fib(n,M=M,T=T,W={W},K={(1<<W)-1}):
    f=0;g=1
    for t in T:
        d=n&K
        if d:
            p,q=t[d]
            f,g=(f*q+(g-f)*p)%M,(f*p+g*q)%M
        n>>=W
        if not n: break
    return f
sys.stdout.write(str(fib(int(sys.argv[1])))+"\\n")
""")
open(f"fib{W}.py","w").write("".join(out))
