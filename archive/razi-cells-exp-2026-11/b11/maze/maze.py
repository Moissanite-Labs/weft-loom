import sys, os, subprocess

SRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int issep(char c){return c=='\n'||c=='\r'||c==' '||c=='\t';}
int main(void){
  size_t cap=1<<22,n=0; char*buf=malloc(cap);
  for(;;){ if(n==cap){cap*=2;buf=realloc(buf,cap);} ssize_t r=read(0,buf+n,cap-n); if(r<=0)break; n+=r; }
  size_t H=0,W=0,i=0;
  while(i<n){ while(i<n&&issep(buf[i]))i++; if(i>=n)break; size_t j=i; while(j<n&&!issep(buf[j]))j++; if(j-i>W)W=j-i; H++; i=j; }
  if(H==0){puts("-1");return 0;}
  size_t P=W+2, T=(H+2)*P; unsigned char*g=malloc(T); memset(g,1,T);
  long s=-1,e=-1; size_t row=0; i=0;
  while(i<n){ while(i<n&&issep(buf[i]))i++; if(i>=n)break; size_t j=i; while(j<n&&!issep(buf[j]))j++;
    size_t base=(row+1)*P+1; unsigned char*gr=g+base;
    for(size_t k=i;k<j;k++){ char c=buf[k]; size_t idx=k-i; if(c=='#')gr[idx]=1; else { gr[idx]=0; if(c=='S')s=base+idx; else if(c=='E')e=base+idx; } }
    row++; i=j; }
  if(s<0||e<0){puts("-1");return 0;} if(s==e){puts("0");return 0;}
  int*q=malloc(sizeof(int)*T); size_t qh=0,qt=0; q[qt++]=(int)s; g[s]=1; g[e]=2;
  int d=0; long off[4]={-1,1,-(long)P,(long)P};
  while(qh<qt){ size_t end=qt; d++;
    while(qh<end){ long p=q[qh++];
      for(int k=0;k<4;k++){ long u=p+off[k]; unsigned char v=g[u]; if(v==0){g[u]=1;q[qt++]=(int)u;} else if(v==2){printf("%d\n",d);return 0;} } } }
  puts("-1"); return 0;
}
'''

def native():
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        exe = os.path.join(d, '_maze_bin3')
        if not os.path.exists(exe):
            src = exe + '.c'
            with open(src, 'w') as f: f.write(SRC)
            r = subprocess.run(['cc', '-O3', '-march=native', '-o', exe, src], capture_output=True)
            if r.returncode != 0 or not os.path.exists(exe): return
        sys.stdout.flush()
        os.execv(exe, [exe])
    except Exception:
        return

def main():
    data = sys.stdin.buffer.read()
    rows = [r for r in data.split() if r]
    if not rows:
        print(-1); return
    H = len(rows); W = max(len(r) for r in rows)
    P = W + 2
    tbl = bytearray(256); tbl[35] = 1; tbl = bytes(tbl)
    wall = b'\x01'
    parts = [wall * P]
    s = e = -1
    for i, r in enumerate(rows):
        parts.append(wall + r.translate(tbl) + wall * (P - 1 - len(r)))
        k = r.find(b'S')
        if k >= 0: s = (i + 1) * P + 1 + k
        k = r.find(b'E')
        if k >= 0: e = (i + 1) * P + 1 + k
    parts.append(wall * P)
    g = bytearray(b''.join(parts))
    if s < 0 or e < 0:
        print(-1); return
    if s == e:
        print(0); return
    g[s] = 1
    g[e] = 2
    cur = [s]
    d = 0
    while cur:
        d += 1
        nxt = []
        app = nxt.append
        for p in cur:
            q = p - 1
            if not g[q]:
                g[q] = 1; app(q)
            elif g[q] == 2:
                print(d); return
            q = p + 1
            if not g[q]:
                g[q] = 1; app(q)
            elif g[q] == 2:
                print(d); return
            q = p - P
            if not g[q]:
                g[q] = 1; app(q)
            elif g[q] == 2:
                print(d); return
            q = p + P
            if not g[q]:
                g[q] = 1; app(q)
            elif g[q] == 2:
                print(d); return
        cur = nxt
    print(-1)

native()
main()
