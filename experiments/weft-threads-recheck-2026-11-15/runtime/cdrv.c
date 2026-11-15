#include "weft_invariants.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static float fb(uint32_t u){ float f; memcpy(&f,&u,4); return f; }
static uint32_t bf(float f){ uint32_t u; memcpy(&u,&f,4); return u; }
int main(int argc,char**argv){ if(argc<2) return 2;
  FILE*fp=fopen(argv[1],"r"); if(!fp){perror("open");return 2;}
  char *line=NULL; size_t cap=0; 
  unsigned long id; size_t n; unsigned r,b,c; int hm;
  while(1){
    if(getline(&line,&cap,fp)<0) break;
    if(sscanf(line,"%lu %zu %u %u %u %d",&id,&n,&r,&b,&c,&hm)!=6){fprintf(stderr,"bad header\n");return 2;}
    float *bw=malloc((n+1)*4),*cw=malloc((n+1)*4); uint8_t*m=malloc(n+1);
    for(int k=0;k<3;k++){
      if(getline(&line,&cap,fp)<0){fprintf(stderr,"eof\n");return 2;}
      char*p=line; for(size_t i=0;i<n;i++){ if(k==2&&!hm) break; unsigned long v=strtoul(p,&p,10);
        if(k==0)bw[i]=fb((uint32_t)v); else if(k==1)cw[i]=fb((uint32_t)v); else m[i]=(uint8_t)v; }
    }
    float budget=fb(b), dist=-1.0f; float before=budget;
    bool ok = hm ? weft_verify_weight_update_safety_masked(bw,cw,m,n,fb(r),&budget,fb(c),&dist)
                 : weft_verify_weight_update_safety(bw,cw,n,fb(r),&budget,fb(c),&dist);
    printf("%lu %d %u %u %u\n",id,ok?1:0,bf(budget),bf(dist),bf(before));
    free(bw);free(cw);free(m);
  }
  return 0;
}
