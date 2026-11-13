import subprocess,sys,time,random,os
print('cpus',os.cpu_count(),len(os.sched_getaffinity(0)))
def run(f,b): return subprocess.run([sys.executable,f],input=b,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
def ref(b):
    a=sorted(map(int,b.split())); return ('\n'.join(map(str,a))+'\n').encode() if a else b''
random.seed(7)
tests=[]
for maxd in (1,2,3,6,7,8,9,12,14,15,16,18):
    for n in (1500,20000):
        ws=[' ','\n','\t','  ','\r\n',' \n ']
        s=''.join(str(random.choice([-1,1])*random.randrange(10**random.randint(0,maxd)))+random.choice(ws) for _ in range(n))
        tests.append(s.encode()); tests.append(b'  '+s.encode().rstrip())
tests.append(b'0 '*3000); tests.append(b'-5\n'*3000+b'x'); tests.append(b'1-2 '*3000); tests.append(b'-0 '*3000+b'007 +3'); tests.append(b' '*5000)
inp=open('data.txt','rb').read(); exp=open('expected.txt','rb').read()
for f in ('sortints.py','d.py','e.py'):
    bad=[i for i,x in enumerate(tests) if run(f,x)!=ref(x)]
    best=9
    for _ in range(7):
        t=time.perf_counter(); o=run(f,inp); best=min(best,time.perf_counter()-t)
    print(f,'bad',bad,'big ok',o==exp,'t',round(best,4))
