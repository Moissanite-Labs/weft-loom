#include "weft_invariants.h"
#include <stdio.h>
#include <stdlib.h>
static float fb(uint32_t u){ float f; memcpy(&f,&u,4); return f; }
int main(int argc,char**argv){ if(argc<3) return 2;
  FILE*f=fopen(argv[1],"r"); unsigned t,m; char buf[256];
  while(fgets(buf,sizeof buf,f)){ if(sscanf(buf,"%u %u",&t,&m)!=2) return 3; bool h=false,e=false;
    bool a=weft_verify_tension_bound(fb(t),fb(m),&h,&e); printf("%d %d %d\n",a,h,e);} fclose(f);
  f=fopen(argv[2],"r"); unsigned long long g,b;
  while(fgets(buf,sizeof buf,f)){ if(sscanf(buf,"%llu %llu",&g,&b)!=2) return 4; uint64_t u,w; weft_royalty_split_u64(g,b,&u,&w); printf("R %llu %llu\n",(unsigned long long)u,(unsigned long long)w);} return 0; }
