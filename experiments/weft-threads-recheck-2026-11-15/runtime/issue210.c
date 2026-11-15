#include "weft_invariants.h"
#include <stdio.h>
static void t(const char*name,const float*b,const float*c,size_t n,float r,float bud,float cost){
  float budget=bud,d=0; bool ok=weft_verify_weight_update_safety(b,c,n,r,&budget,cost,&d);
  printf("%-52s accepted=%d budget_before=%g budget_after=%g\n",name,ok,bud,budget);}
int main(void){
  float b[2]={0,0}, c[2]={0.1f,0}, nanw[2]={NAN,0}, far[2]={50,0};
  t("budget 10, cost 20 (insufficient)",b,c,2,1,10,20);
  t("budget 0, cost 1",b,c,2,1,0,1);
  t("budget -1, cost 1",b,c,2,1,-1,1);
  t("budget 10, cost 1, radius -1",b,c,2,-1,10,1);
  t("budget 10, cost 1, radius -1, NaN weight",b,nanw,2,-1,10,1);
  t("budget 10, cost 1, radius 1, distance 50 (exceeded)",b,far,2,1,10,1);
  t("budget 10, cost -1 (negative cost)",b,c,2,1,10,-1);
  t("budget 10, cost 1, NaN weight, radius 1",b,nanw,2,1,10,1);
  t("budget 10, cost 1, length 0",b,c,0,1,10,1);
  t("budget 10, cost 1, radius 1, distance 0.1 (accept)",b,c,2,1,10,1);
  return 0; }
