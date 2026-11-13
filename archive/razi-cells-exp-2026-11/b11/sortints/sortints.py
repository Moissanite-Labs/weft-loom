import sys, os
SRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
int main(){
  size_t cap=1<<20,n=0; char*buf=malloc(cap);
  for(;;){ if(n==cap){cap*=2;buf=realloc(buf,cap);} ssize_t r=read(0,buf+n,cap-n); if(r<=0)break; n+=r;}
  size_t kc=1<<16,k=0; uint64_t*a=malloc(kc*8);
  char*p=buf,*e=buf+n;
  while(p<e){
    while(p<e && (unsigned char)*p<=' ')p++;
    if(p>=e)break;
    int neg=0; if(*p=='-'){neg=1;p++;} else if(*p=='+')p++;
    uint64_t v=0; while(p<e && *p>='0'&&*p<='9'){v=v*10+(*p-'0');p++;}
    int64_t s=neg?-(int64_t)v:(int64_t)v;
    if(k==kc){kc*=2;a=realloc(a,kc*8);}
    a[k++]=(uint64_t)s ^ 0x8000000000000000ULL;
  }
  uint64_t*b=malloc(k*8+8);
  for(int sh=0;sh<64;sh+=16){
    size_t cnt[65536]; memset(cnt,0,sizeof cnt);
    for(size_t i=0;i<k;i++)cnt[(a[i]>>sh)&65535]++;
    size_t i0=0; for(;i0<65536;i0++) if(cnt[i0]==k) break;
    if(i0<65536) continue;
    size_t sum=0; for(int i=0;i<65536;i++){size_t c=cnt[i];cnt[i]=sum;sum+=c;}
    for(size_t i=0;i<k;i++){uint64_t x=a[i];b[cnt[(x>>sh)&65535]++]=x;}
    uint64_t*t=a;a=b;b=t;
  }
  char*out=malloc(k*22+16); char*o=out; char tmp[24];
  for(size_t i=0;i<k;i++){
    int64_t v=(int64_t)(a[i]^0x8000000000000000ULL);
    uint64_t u; if(v<0){*o++='-';u=(uint64_t)(-(v+1))+1;} else u=(uint64_t)v;
    int l=0; do{tmp[l++]='0'+u%10;u/=10;}while(u);
    while(l)*o++=tmp[--l];
    *o++='\n';
  }
  size_t tot=o-out,w=0; while(w<tot){ssize_t r=write(1,out+w,tot-w); if(r<=0)break; w+=r;}
  return 0;
}
'''
def main():
    d = os.path.dirname(os.path.abspath(__file__))
    binp = os.path.join(d, '_sortints_bin')
    if not os.path.exists(binp):
        try:
            import subprocess, tempfile
            src = os.path.join(d, '_sortints.c')
            with open(src, 'w') as f: f.write(SRC)
            tmp = binp + '.tmp%d' % os.getpid()
            subprocess.run(['gcc', '-O2', '-o', tmp, src], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.rename(tmp, binp)
        except Exception:
            pass
    if os.path.exists(binp):
        sys.stdout.flush()
        os.execv(binp, [binp])
    # fallback
    os.environ.setdefault('KMP_WARNINGS','0'); os.environ.setdefault('OMP_NUM_THREADS','1')
    data = sys.stdin.buffer.read()
    import numpy as np
    arr = np.fromstring(data, dtype=np.int64, sep=' ')
    arr.sort()
    sys.stdout.buffer.write(('\n'.join(map(str, arr.tolist())) + '\n').encode('ascii'))
main()
