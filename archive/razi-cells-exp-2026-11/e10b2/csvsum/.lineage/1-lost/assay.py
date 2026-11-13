import subprocess,time,sys
exp=open('expected.txt').read()
def run():
    t=time.perf_counter()
    out=subprocess.run([sys.executable,'csvsum.py'],stdin=open('data.csv','rb'),capture_output=True,text=True).stdout
    return time.perf_counter()-t,out
run()  # warm-up (file cache, pyc)
ts=[]
for _ in range(7):
    dt,out=run()
    if out!=exp:
        print(0); sys.exit(0)
    ts.append(dt)
print('%.4f'%(1.0/min(ts)))
