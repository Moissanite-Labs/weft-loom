import json, random, zlib, bz2, lzma, sys

def corpus():
    random.seed(1234)
    common = ('the of and to in a is that it was for on are as with his they at be this have from one had by word but not what all were we when your can said there use an each which she do how their if will up other about out many then them these so some her would make like him into time has look two more write go see number no way could people my than first water been call who oil its now find long down day did get come made may part').split()
    parts=[]
    for _ in range(120):
        n=random.randint(6,18)
        ws=[]
        for _ in range(n):
            w=random.choice(common)
            if random.random()<0.08: w=w.capitalize()
            ws.append(w)
        s=' '.join(ws)
        s=s[0].upper()+s[1:]+random.choice(['.','.','!','?','.'])
        parts.append(s)
    text=' '.join(parts)
    objs=[]
    for i in range(60):
        objs.append({'id':i,'name':random.choice(common)+'-'+str(random.randint(0,999)),'active':random.random()<0.5,'score':round(random.uniform(0,100),3),'tags':[random.choice(common) for _ in range(random.randint(0,4))],'meta':{'created':'2024-0%d-1%d'%(random.randint(1,9),random.randint(0,9)),'owner':random.choice(common),'nested':{'x':random.randint(0,1000),'y':random.randint(0,1000)}}})
    js=json.dumps(objs,indent=1)
    js2=json.dumps(objs,separators=(',',':'))
    return (text+'\n'+js+'\n'+js2).encode()

data=corpus()
print('len',len(data))

def show(name,b):
    print('%-28s %7d %7.4f'%(name,len(b),len(data)/len(b)))

show('zlib9',zlib.compress(data,9))
show('bz2-9',bz2.compress(data,9))
show('xz-e',lzma.compress(data,preset=9|lzma.PRESET_EXTREME))
show('alone-e',lzma.compress(data,format=lzma.FORMAT_ALONE,preset=9|lzma.PRESET_EXTREME))

for lc in (0,1,2,3,4):
    for pb in (0,1,2):
        for lp in (0,):
            if lc+lp>4: continue
            f=[{'id':lzma.FILTER_LZMA1,'preset':9|lzma.PRESET_EXTREME,'lc':lc,'lp':lp,'pb':pb}]
            try:
                b=lzma.compress(data,format=lzma.FORMAT_RAW,filters=f)
            except Exception as e:
                print('err',lc,lp,pb,e); continue
            show('raw lc%d lp%d pb%d'%(lc,lp,pb),b)
