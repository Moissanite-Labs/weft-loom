import collections
L=open('big.txt').read().split()
h=len(L);w=len(L[0])
D={(0,0):0};q=collections.deque([(0,0)])
while q:
    x,y=q.popleft()
    for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0<=a<h and 0<=b<w and L[a][b]!='#' and (a,b) not in D:
            D[a,b]=D[x,y]+1;q.append((a,b))
print(D.get((h-1,w-1),-1))
