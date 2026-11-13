import sys
from collections import deque
L=[l.rstrip('\n') for l in open('big.txt') if l.strip()]
h=len(L);w=len(L[0])
D={(0,0):0};q=deque([(0,0)])
r=-1
while q:
    y,x=q.popleft()
    if L[y][x]=='E': r=D[(y,x)];break
    for a,b in((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
        if 0<=a<h and 0<=b<w and L[a][b]!='#' and (a,b) not in D:
            D[(a,b)]=D[(y,x)]+1;q.append((a,b))
print(r)
