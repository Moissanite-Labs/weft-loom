import sys,os,pickle
from collections import defaultdict
def work(data,s,e):
    sums=defaultdict(float)
    flat=data[s:e].replace(b'\n',b',').split(b',')
    if flat and flat[-1]==b'': flat.pop()
    for cat,v in zip(flat[1::3],map(float,flat[2::3])):
        sums[cat]+=v
    return sums
def main():
    data=sys.stdin.buffer.read()
    n=len(data)
    h=data.find(b'\n')+1
    N=os.cpu_count() or 1
    if N<2 or n-h<500000:
        sums=work(data,h,n)
    else:
        bounds=[h]
        for i in range(1,N):
            p=data.find(b'\n',h+(n-h)*i//N)
            bounds.append(n if p<0 else p+1)
        bounds.append(n)
        kids=[]
        for i in range(N):
            r,w=os.pipe()
            pid=os.fork()
            if pid==0:
                os.close(r)
                d=dict(work(data,bounds[i],bounds[i+1]))
                with os.fdopen(w,'wb') as f: f.write(pickle.dumps(d))
                os._exit(0)
            os.close(w)
            kids.append((pid,r))
        sums=defaultdict(float)
        for pid,r in kids:
            with os.fdopen(r,'rb') as f: d=pickle.load(f)
            os.waitpid(pid,0)
            for k,v in d.items(): sums[k]+=v
    sys.stdout.write(''.join('%s,%.2f\n'%(k.decode(),v) for k,v in sorted(sums.items())))
main()
