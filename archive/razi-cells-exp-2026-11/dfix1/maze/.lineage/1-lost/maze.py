import sys
def main():
    L=sys.stdin.read().split()
    W=len(L[0])+1
    t=''.join(r+'#' for r in L)
    s=t.index('S');e=t.index('E')
    o=int(t.translate({35:48,46:49,83:48,69:49})[::-1],2)
    v=fr=1<<s;eb=1<<e;d=0
    while fr:
        d+=1
        n=((fr<<1)|(fr>>1)|(fr<<W)|(fr>>W))&o&~v
        if n&eb:
            print(d);return
        v|=n;fr=n
    print(-1)
main()
