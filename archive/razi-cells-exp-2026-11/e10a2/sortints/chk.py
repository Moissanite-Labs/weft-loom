import subprocess,sys,time,random
exp=open('expected.txt','rb').read()
inp=open('data.txt','rb').read()
def run(f,b):
    return subprocess.run([sys.executable,f],input=b,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
def ref(b):
    a=sorted(map(int,b.split()))
    return ('\n'.join(map(str,a))+'\n').encode() if a else b''
random.seed(7)
tests=[]
for mag,n in [(10,3000),(10**6,5000),(10**9,5000),(10**15,4000),(10**17,3000),(10**25,3000),(1,5000)]:
    seps=[' ','\n','\t','  ','\r\n',' \n ']
    s=''.join(str(random.randint(-mag,mag))+random.choice(seps) for _ in range(n))
    tests.append(s.encode()); tests.append((' \n'+s.strip()).encode())
tests.append(('+5 007 -0 '+' '.join(str(random.randint(-99,99)) for _ in range(3000))).encode())
tests.append(b' '*5000)
for f in sys.argv[1:]:
    bad=[i for i,t in enumerate(tests) if run(f,t)!=ref(t)]
    best=9
    ok=True
    for _ in range(7):
        t=time.perf_counter(); o=run(f,inp); d=time.perf_counter()-t
        ok&=(o==exp); best=min(best,d)
    print(f,'bad',bad,'big ok',ok,'t',round(best,4))
