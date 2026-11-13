import subprocess, sys, time, os, random, collections
# build workload if missing
path = 'bench.csv'
if not os.path.exists(path) or os.path.getsize(path) < 50_000_000:
    random.seed(7)
    cats = ['alpha','beta','gamma','delta','epsilon','zeta','eta','theta','iota','kappa']
    with open(path,'w') as f:
        f.write('id,cat,val\n')
        for i in range(2_000_000):
            f.write('%d,%s,%.10f\n' % (i, cats[i % 10], random.random()*1000))
t0=time.time()
r = subprocess.run([sys.executable,'csvsum.py'], stdin=open(path,'rb'), capture_output=True)
el = time.time()-t0
if r.returncode != 0:
    print(0.0); sys.exit(0)
out = r.stdout.decode().strip().split('\n')
# correct check against independent reference
sums=collections.defaultdict(float)
with open(path,'rb') as f:
    f.readline()
    for line in f:
        p=line.split(b',')
        sums[p[1].decode()] += float(p[2])
exp = [c+','+format(sums[c],'.2f') for c in sorted(sums)]
if out != exp:
    print(0.0); sys.exit(0)
# score: rows per second scaled, heavy enough ~0.9s baseline -> score around speed
print(round(2_000_000/el, 1))
