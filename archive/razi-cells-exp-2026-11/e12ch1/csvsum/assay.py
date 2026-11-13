import subprocess,time
t=time.time()
o=subprocess.run("python3 csvsum.py <data.csv",shell=True,capture_output=True).stdout
t=time.time()-t
print(1/t if o==open("exp.txt","rb").read() and o else 0)
