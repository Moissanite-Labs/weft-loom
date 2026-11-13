def cents(s):
    s=s.strip()
    neg=s.startswith('-')
    if neg: s=s[1:]
    if '.' in s:
        w,f=s.split('.')
        f=(f+'00')[:2]
    else:
        w,f=s,'00'
    v=int(w)*100+int(f)
    return -v if neg else v

sums={}
with open('data.csv') as f:
    next(f)
    for line in f:
        p=line.rstrip('\n').split(',')
        c=p[1]; v=cents(p[2])
        sums[c]=sums.get(c,0)+v
with open('expected.txt','w') as f:
    for c in sorted(sums):
        t=sums[c]
        sign='-' if t<0 else ''
        t=abs(t)
        f.write('%s,%s%d.%02d\n'%(c,sign,t//100,t%100))
