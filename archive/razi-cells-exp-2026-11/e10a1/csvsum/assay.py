import subprocess,time,sys
exp=open('expected.txt','rb').read()
best=1e9
for _ in range(9):
    f=open('data.csv','rb')
    t=time.perf_counter()
    r=subprocess.run([sys.executable,'csvsum.py'],stdin=f,capture_output=True)
    dt=time.perf_counter()-t
    f.close()
    if r.returncode!=0 or r.stdout!=exp:
        print(0); sys.exit(0)
    best=min(best,dt)
print('%.4f'%(1.0/best))
