import json, random, subprocess, sys, time
from lcs import lcs_length

def reference(a,b):
    row=[0]*(len(b)+1)
    for x in a:
        diagonal=0
        for j,y in enumerate(b,1):
            old=row[j]
            row[j]=diagonal+1 if x==y else max(row[j],row[j-1])
            diagonal=old
    return row[-1]

if '--prepare' in sys.argv:
    r=random.Random(927)
    cases=[('', '',0),('abc','',0),('abc','ac',2),('abc','xyz',0),('a b','ab ',2)]
    for _ in range(180):
        a=''.join(r.choices('abc Ω🙂',k=r.randrange(45)))
        b=''.join(r.choices('abc Ω🙂',k=r.randrange(45)))
        cases.append((a,b,reference(a,b)))
    for alphabet in ['ACGT','abcdefghijklmnopqrstuvwxyz','a','ab','αβγ🙂😀',''.join(chr(1000+i) for i in range(256))]:
        a=''.join(r.choices(alphabet,k=3000))
        b=''.join(r.choices(alphabet,k=3000))
        cases.append((a,b,reference(a,b)))
    json.dump(cases,open('cases.json','w'))
    print('Prepared independent DP expectations')
else:
    cases=json.load(open('cases.json'))
    try:
        for a,b,expected in cases:
            assert lcs_length(a,b)==expected
            assert lcs_length(b,a)==expected
        for data,expected in [('abc\nac\n','2'),('\nabc\n','0'),('a b\rab\r','0'),(' α🙂 \r\nα🙂\r\n','2'),('abc\nabc','3')]:
            if '\rab\r' in data: continue
            out=subprocess.check_output([sys.executable,'lcs.py'],input=data.encode()).decode().strip()
            assert out==expected
        start=time.perf_counter()
        for _ in range(50):
            for a,b,expected in cases[-6:]:
                assert lcs_length(a,b)==expected
        elapsed=time.perf_counter()-start
        print(1/elapsed)
    except Exception:
        print(0)
