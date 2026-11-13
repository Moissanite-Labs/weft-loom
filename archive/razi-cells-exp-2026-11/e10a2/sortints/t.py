import subprocess,sys,random,time
def run(f,b):
    return subprocess.run([sys.executable,f],input=b,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL).stdout
def ref(b):
    a=sorted(map(int,b.split()))
    return ('\n'.join(map(str,a))+'\n').encode() if a else b''
random.seed(7)
cases=[b'',b'3 -1\n2\t-5  10\n',b' '*5000,b'5'*3+b' '*5000+b'-2']
def mk(lo,hi,n,seps,extra=()):
    t=[str(random.randint(lo,hi)) for _ in range(n)]+list(extra)
    random.shuffle(t)
    return ''.join(x+random.choice(seps) for x in t).encode()
cases.append(mk(-50,50,3000,['\n']))
cases.append(mk(-50,50,3000,[' ','\n','\t','\r\n','  \n ','\x0b','\x0c'])[:-1].rstrip()+b'')
cases.append(b'  \n'+mk(-10**15,10**15,3000,[' ','\n']))
cases.append(mk(-10**16+1,10**16-1,3000,[' ']).rstrip())
cases.append(mk(0,9,5000,['\n']))
cases.append(mk(-10**8,10**8,3000,['\n'],['0','0','-1','99999999','100000000','-99999999','-100000000','9999999999999999','-9999999999999999']))
cases.append(mk(-10**30,10**30,2000,['\n']))
cases.append(mk(-100,100,3000,['\n'],['+5']))
cases.append(mk(-100,100,3000,['\n'],['007']))
cases.append(mk(-100,100,3000,['\n'],['-0']))
cases.append(mk(-100,100,3000,['\n'],['-007']))
cases.append(mk(-100,100,3000,['\n'],['1_000']))
cases.append(mk(-10**12,10**12,200000,['\n']))
for f in sys.argv[1:]:
    bad=[i for i,c in enumerate(cases) if run(f,c)!=ref(c)]
    inp=open('data.txt','rb').read(); exp=open('expected.txt','rb').read()
    best=9
    for _ in range(4):
        t=time.perf_counter(); o=run(f,inp); best=min(best,time.perf_counter()-t)
    print(f,'bad',bad,'big ok',o==exp,'t',round(best,4))
