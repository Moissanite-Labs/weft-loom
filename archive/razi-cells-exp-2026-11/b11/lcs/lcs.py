import sys, os, subprocess

CSRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
int main(void){
  size_t cap=1<<20,len=0; char*buf=malloc(cap); size_t r;
  while((r=fread(buf+len,1,cap-len,stdin))>0){len+=r; if(len==cap){cap*=2;buf=realloc(buf,cap);}}
  char*a=buf,*b; size_t la,lb;
  char*nl=memchr(buf,'\n',len);
  if(nl){la=nl-buf;b=nl+1;char*nl2=memchr(b,'\n',len-(b-buf));lb=nl2?(size_t)(nl2-b):len-(b-buf);}
  else{la=len;b=buf+len;lb=0;}
  if(la&&a[la-1]=='\r')la--; if(lb&&b[lb-1]=='\r')lb--;
  if(la<lb){char*t=a;a=b;b=t;size_t s=la;la=lb;lb=s;}
  size_t n=lb; if(n==0){puts("0");return 0;}
  size_t W=(n+63)/64;
  uint64_t*pm=calloc(256*W,8); uint64_t*V=malloc(W*8);
  for(size_t j=0;j<n;j++)pm[(unsigned char)b[j]*W+j/64]|=1ULL<<(j%64);
  for(size_t w=0;w<W;w++)V[w]=~0ULL;
  for(size_t i=0;i<la;i++){
    const uint64_t*M=pm+(unsigned char)a[i]*W; uint64_t carry=0;
    for(size_t w=0;w<W;w++){
      uint64_t v=V[w],u=v&M[w],x=v^u;
      uint64_t s=v+u; uint64_t c1=s<u; uint64_t s2=s+carry; uint64_t c2=s2<carry;
      carry=c1|c2;
      V[w]=s2|x;
    }
  }
  size_t cnt=0;
  for(size_t w=0;w<W;w++){uint64_t v=V[w]; if(w==W-1&&(n%64))v|=~0ULL<<(n%64); cnt+=__builtin_popcountll(~v);}
  printf("%zu\n",cnt);
  return 0;
}
'''

def lcs_py(a, b):
    if len(a) < len(b):
        a, b = b, a
    n = len(b)
    if n == 0:
        return 0
    mask = (1 << n) - 1
    pm = {}
    bit = 1
    for c in b:
        pm[c] = pm.get(c, 0) | bit
        bit <<= 1
    pairs = {c: (m, mask ^ m) for c, m in pm.items()}
    V = mask
    get = pairs.get
    for p in map(get, a):
        if p is None:
            continue
        M, NM = p
        V = (V + (V & M)) | (V & NM)
    return n - (V & mask).bit_count()

def lcs(a, b):
    return lcs_py(a, b)

def binary():
    d = os.path.dirname(os.path.abspath(__file__))
    exe = os.path.join(d, "_lcs_bin3")
    if os.path.exists(exe):
        return exe
    try:
        src = os.path.join(d, "_lcs_%d.c" % os.getpid())
        tmp = exe + ".%d" % os.getpid()
        with open(src, "w") as f:
            f.write(CSRC)
        r = subprocess.run(["gcc", "-O3", "-march=native", "-o", tmp, src], capture_output=True)
        if r.returncode != 0:
            r = subprocess.run(["gcc", "-O2", "-o", tmp, src], capture_output=True)
        os.unlink(src)
        if r.returncode != 0:
            return None
        os.replace(tmp, exe)
        return exe
    except Exception:
        return None

def main():
    raw = sys.stdin.buffer.read()
    if raw.isascii():
        exe = binary()
        if exe:
            r = subprocess.run([exe], input=raw, capture_output=True)
            if r.returncode == 0 and r.stdout.strip().isdigit():
                sys.stdout.write(r.stdout.decode())
                return
    data = raw.decode("utf-8", "surrogateescape").split("\n")
    a = data[0] if len(data) > 0 else ""
    b = data[1] if len(data) > 1 else ""
    print(lcs_py(a, b))

if __name__ == "__main__":
    main()
