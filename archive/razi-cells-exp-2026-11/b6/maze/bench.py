import subprocess,sys,time
with open('large.txt','rb') as f:
    start=time.perf_counter()
    result=subprocess.run([sys.executable,'maze.py'],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    elapsed=time.perf_counter()-start
print(1/elapsed if result.returncode==0 and result.stdout.strip()==b'3998' else 0)
