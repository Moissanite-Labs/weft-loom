import json,sys
def walk(a,b,p,out):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a: out.append((p+"/"+k,"MISSING_IN_COMMITTED",b[k]))
            elif k not in b: out.append((p+"/"+k,a[k],"MISSING_IN_FRESH"))
            else: walk(a[k],b[k],p+"/"+k,out)
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b): out.append((p,"len%d"%len(a),"len%d"%len(b)))
        for i,(x,y) in enumerate(zip(a,b)): walk(x,y,p+"[%d]"%i,out)
    else:
        out.append((p,a,b)) if a!=b else None
        out.append(None) if False else None
def cmp(c,f,skip=()):
    a=json.load(open(c)); b=json.load(open(f)); out=[]; walk(a,b,"",out)
    out=[o for o in out if o and not any(s in o[0] for s in skip)]
    mx=0
    for p,x,y in out:
        if isinstance(x,(int,float)) and isinstance(y,(int,float)): mx=max(mx,abs(x-y))
    return out,mx
if __name__=="__main__":
    c,f=sys.argv[1:3]; skip=sys.argv[3:]
    out,mx=cmp(c,f,skip)
    print(c.split('/')[-1],"ndiff=",len(out),"maxabs(numeric)=",mx)
    for o in out[:40]: print("  ",o)
