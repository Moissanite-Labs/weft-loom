import sys, numpy as np
def main():
    data = sys.stdin.buffer.read()
    i = data.find(b'\n')
    toks = data[i+1:].replace(b',', b' ').split()
    ca = np.array(toks[1::3])
    va = np.array(toks[2::3], dtype=np.float64)
    L = ca.dtype.itemsize
    if L <= 8:
        v = ca.view(np.uint8).reshape(-1, L)
        key = np.zeros(len(ca), dtype=np.uint64)
        for k in range(L):
            key = (key << np.uint64(8)) | v[:, k].astype(np.uint64)
        u, first, inv = np.unique(key, return_index=True, return_inverse=True)
        sums = np.bincount(inv, weights=va, minlength=len(u))
        names = ca[first]
    else:
        names, inv = np.unique(ca, return_inverse=True)
        sums = np.bincount(inv, weights=va, minlength=len(names))
    sys.stdout.write('\n'.join(names[k].decode()+','+format(sums[k],'.2f') for k in range(len(names)))+'\n')
main()
