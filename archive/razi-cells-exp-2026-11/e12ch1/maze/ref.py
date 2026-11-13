import sys
from collections import deque
L=open('m.txt').read().split();h=len(L);w=len(L[0])
for y in range(h):
  for x in range(w):
    if L[y][x]=='S':s=(y,x)
dist={s:0};q=deque([s])
while q:
  y,x=q.popleft()
  if L[y][x]=='E':print(dist[(y,x)]);sys.exit()
  for a,b in((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
    if 0<=a<h and 0<=b<w and L[a][b]!='#' and (a,b) not in dist:dist[(a,b)]=dist[(y,x)]+1;q.append((a,b))
print(-1)
