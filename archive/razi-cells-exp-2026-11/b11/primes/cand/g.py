import sys, os
SRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
int main(int argc,char**argv){
  long n=atol(argv[1]);
  if(n<3){printf("0\n");return 0;}
  long r=(long)sqrt((double)n); while(r*r>n)r--; while((r+1)*(r+1)<=n)r++;
  long m=r/2+1;
  unsigned char*s=calloc(m+1,1);
  long cnt=1, np=0;
  long *pr=malloc(sizeof(long)*(m+2));
  for(long i=1;i<m;i++){ if(!s[i]){ long p=2*i+1; pr[np++]=p; for(long j=p*p/2;j<m;j+=p)s[j]=1; } }
  long hi=(n-2)/2;
  const long SEG=32768;
  unsigned char*seg=malloc(SEG);
  long *nxt=malloc(sizeof(long)*(np+1));
  for(long k=0;k<np;k++){ long p=pr[k]; nxt[k]=p*p/2; }
  for(long lo=1; lo<=hi; lo+=SEG){
    long end=lo+SEG; if(end>hi+1)end=hi+1;
    long len=end-lo;
    memset(seg,0,len);
    for(long k=0;k<np;k++){
      long p=pr[k]; long j=nxt[k];
      if(p*p/2>=end) break;
      for(;j<end;j+=p)seg[j-lo]=1;
      nxt[k]=j;
    }
    long c=0; for(long i=0;i<len;i++)c+=seg[i];
    cnt+=len-c;
  }
  printf("%ld\n",cnt);
  return 0;
}
'''
def py(n):
    from math import isqrt
    if n < 3: return 0
    size = n//2
    s = bytearray([1])*size; s[0]=0
    for i in range(1, isqrt(n)//2+1):
        if s[i]:
            p=2*i+1; st=p*p//2
            s[st::p]=bytes(len(range(st,size,p)))
    return s.count(1)+1
def main():
    n = int(sys.argv[1])
    d = os.path.dirname(os.path.abspath(__file__))
    b = os.path.join(d, '_primes_bin')
    if not os.path.exists(b):
        try:
            import subprocess, tempfile
            c = os.path.join(d, '_primes_src.c')
            with open(c, 'w') as f: f.write(SRC)
            t = b + '.tmp%d' % os.getpid()
            for cc in ('cc', 'gcc', 'clang'):
                if subprocess.run([cc, '-O2', '-o', t, c, '-lm'], capture_output=True).returncode == 0:
                    os.rename(t, b); break
        except Exception:
            pass
    if os.path.exists(b):
        try:
            os.execv(b, [b, str(n)])
        except Exception:
            pass
    print(py(n))
main()
