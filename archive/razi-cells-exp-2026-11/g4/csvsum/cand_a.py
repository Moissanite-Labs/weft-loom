import sys, numpy as np
def main():
    data = sys.stdin.buffer.read()
    i = data.find(b'\n')
    toks = data[i+1:].replace(b',', b' ').split()
    ca = np.array(toks[1::3])
    va = np.array(toks[2::3], dtype=np.float64)
    u, inv = np.unique(ca, return_inverse=True)
    sums = np.bincount(inv, weights=va, minlength=len(u))
    sys.stdout.write('\n'.join(u[k].decode()+','+format(sums[k],'.2f') for k in range(len(u)))+'\n')
main()
