import sys
import numpy as np
def main():
    buf=sys.stdin.buffer.read()
    buf=buf[buf.index(b'\n')+1:]
    t=buf.replace(b'\n',b',').split(b',')
    if len(t)%3: t=t[:len(t)-len(t)%3]
    vals=np.array(t[2::3]).astype(np.float64)
    cats=np.array(t[1::3])
    uk,inv=np.unique(cats,return_inverse=True)
    sums=np.bincount(inv,weights=vals,minlength=len(uk))
    names=[k.decode() for k in uk.tolist()]
    order=sorted(range(len(names)),key=lambda i:names[i])
    sys.stdout.write(''.join("%s,%.2f\n"%(names[i],sums[i]) for i in order))
main()
