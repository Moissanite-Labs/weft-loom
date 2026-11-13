import subprocess, sys, time, random
# correctness: big.txt must give 1948; small random cases vs reference
def ref(a,b):
    prev=[0]*(len(b)+1)
    for x in a:
        cur=[0]
        for j,y in enumerate(b):
            cur.append(prev[j]+1 if x==y else max(prev[j+1],cur[j]))
        prev=cur
    return prev[-1]
def run(inp):
    return subprocess.run([sys.executable,"lcs.py"],input=inp,capture_output=True,text=True).stdout.strip()
big=open("big.txt").read()
if run(big)!="1948": print(0); sys.exit(0)
random.seed(7)
for t in range(5):
    a="".join(random.choice("abc") for _ in range(random.randint(0,30)))
    b="".join(random.choice("abc") for _ in range(random.randint(0,30)))
    if run(a+"\n"+b+"\n")!=str(ref(a,b)): print(0); sys.exit(0)
# timing: heavy workload, 40000-char strings
random.seed(3)
A="".join(random.choice("ACGT") for _ in range(40000))
B="".join(random.choice("ACGT") for _ in range(40000))
inp=A+"\n"+B+"\n"
t0=time.time()
out=run(inp)
dt=time.time()-t0
if not out.isdigit() or int(out)<20000: print(0); sys.exit(0)
print(1000.0/dt)
