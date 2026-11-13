from collections import deque
L=open('m.txt').read().split()
n=len(L);D={(0,0):0};q=deque([(0,0)]);r=-1
while q:
    x,y=q.popleft()
    if L[x][y]=='E':r=D[(x,y)];break
    for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0<=a<n and 0<=b<n and L[a][b]!='#' and (a,b) not in D:D[(a,b)]=D[(x,y)]+1;q.append((a,b))
print(r)
