import subprocess, sys, time, collections, os
if not os.path.exists('ref.txt'):
    sums=collections.defaultdict(float)
    with open('bench.csv','rb') as f:
        f.readline()
        for line in f:
            p=line.split(b',')
            sums[p[1].decode()] += float(p[2])
    exp=[c+','+format(sums[c],'.2f') for c in sorted(sums)]
    open('ref.txt','w').write('\n'.join(exp)+'\n')
exp=open('ref.txt').read().strip()
for cand in sys.argv[1:]:
    best=9e9; ok=False; msg=''
    for _ in range(2):
        t0=time.time()
        r=subprocess.run([sys.executable,cand],stdin=open('bench.csv','rb'),capture_output=True)
        el=time.time()-t0
        best=min(best,el)
        if r.returncode!=0:
            msg='RC=%d %s'%(r.returncode, r.stderr.decode()[-300:].replace('\n',' | ')); break
        out=r.stdout.decode().strip()
        ok = (out==exp)
        if not ok:
            a=out.split('\n'); b=exp.split('\n')
            msg=str([x for x in zip(a,b) if x[0]!=x[1]][:4])
    print('%-9s rows/s=%-10s %-8s %.3fs %s'%(cand, round(2e6/best,0), 'exact' if ok else 'MISMATCH', best, msg))
