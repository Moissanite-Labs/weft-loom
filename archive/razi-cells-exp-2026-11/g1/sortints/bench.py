import subprocess, time, sys, hashlib
ref = None
for c in sys.argv[1:]:
    t = time.perf_counter()
    with open('test.txt','rb') as fin, open('out_'+c+'.txt','wb') as fout:
        r = subprocess.run([sys.executable, c], stdin=fin, stdout=fout)
    dt = time.perf_counter()-t
    h = hashlib.md5(open('out_'+c+'.txt','rb').read()).hexdigest()
    if ref is None: ref = h
    print(c, round(dt,3), 'OK' if h==ref else 'BAD', h)
