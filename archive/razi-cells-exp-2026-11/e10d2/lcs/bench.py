import random, subprocess, sys, time
random.seed(7)
N=60000
a=''.join(random.choice('abcd') for _ in range(N))
b=''.join(random.choice('abcd') for _ in range(N))
inp=a+"\n"+b+"\n"
EXPECT=open("expect.txt").read().strip()
t=time.time()
out=subprocess.run([sys.executable,'lcs.py'],input=inp,capture_output=True,text=True).stdout.strip()
dt=time.time()-t
if len(sys.argv)>1: print(out, dt); sys.exit()
print(1000/dt if out==EXPECT else 0)
