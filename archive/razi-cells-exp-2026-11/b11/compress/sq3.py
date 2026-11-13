import lzma, re
TOK = re.compile(rb' ?[A-Za-z]+|[0-9]+|[^A-Za-z0-9]+')
TOP=0xFFFFFFFF; HALF=0x80000000; Q=0x40000000; Q3=0xC0000000
LIM=1<<16

class Fen:
    __slots__=('n','t','c','tot')
    def __init__(s,n):
        s.n=n; s.t=[0]*(n+1); s.c=[0]*n; s.tot=0
    def add(s,i,v):
        s.c[i]+=v; s.tot+=v; i+=1; n=s.n; t=s.t
        while i<=n: t[i]+=v; i+=i&-i
    def prefix(s,i):
        r=0; t=s.t
        while i>0: r+=t[i]; i-=i&-i
        return r
    def find(s,c):
        pos=0; bit=1<<(s.n.bit_length()-1); t=s.t; n=s.n
        while bit:
            nxt=pos+bit
            if nxt<=n and t[nxt]<=c: pos=nxt; c-=t[nxt]
            bit>>=1
        return pos
    def halve(s):
        c=s.c; n=s.n; t=[0]*(n+1); tot=0
        for i in range(n):
            if c[i]: c[i]=(c[i]+1)>>1
            tot+=c[i]
        for i in range(n):
            if c[i]:
                j=i+1
                while j<=n: t[j]+=c[i]; j+=j&-j
        s.t=t; s.tot=tot
    def bump(s,i,v=1):
        s.add(i,v)
        if s.tot>=LIM: s.halve()

class Enc:
    def __init__(s): s.low=0; s.high=TOP; s.pend=0; s.bits=[]
    def enc(s,lo,hi,tot):
        r=s.high-s.low+1
        s.high=s.low+r*hi//tot-1; s.low=s.low+r*lo//tot
        b=s.bits
        while True:
            if s.high<HALF:
                b.append(0); b.extend([1]*s.pend); s.pend=0
            elif s.low>=HALF:
                b.append(1); b.extend([0]*s.pend); s.pend=0; s.low-=HALF; s.high-=HALF
            elif s.low>=Q and s.high<Q3:
                s.pend+=1; s.low-=Q; s.high-=Q
            else: break
            s.low*=2; s.high=s.high*2+1
    def finish(s):
        s.pend+=1
        if s.low<Q: s.bits.append(0); s.bits.extend([1]*s.pend)
        else: s.bits.append(1); s.bits.extend([0]*s.pend)
        b=s.bits; b.extend([0]*(-len(b)%8))
        return int(''.join(map(str,b)),2).to_bytes(len(b)//8,'big') if b else b''

class Dec:
    def __init__(s,data):
        s.bits=bin(int.from_bytes(data,'big'))[2:].zfill(len(data)*8) if data else ''
        s.bits+='0'*64; s.i=32
        s.low=0; s.high=TOP; s.val=int(s.bits[:32],2)
    def get(s,tot):
        r=s.high-s.low+1
        return ((s.val-s.low+1)*tot-1)//r
    def upd(s,lo,hi,tot):
        r=s.high-s.low+1
        s.high=s.low+r*hi//tot-1; s.low=s.low+r*lo//tot
        bits=s.bits
        while True:
            if s.high<HALF: pass
            elif s.low>=HALF: s.low-=HALF; s.high-=HALF; s.val-=HALF
            elif s.low>=Q and s.high<Q3: s.low-=Q; s.high-=Q; s.val-=Q
            else: break
            s.low*=2; s.high=s.high*2+1; s.val=s.val*2+(bits[s.i]=='1'); s.i+=1

def _code(e,f,sym):
    lo=f.prefix(sym); e.enc(lo,lo+f.c[sym],f.tot); f.bump(sym)
def _decode(d,f):
    sym=f.find(d.get(f.tot)); lo=f.prefix(sym); d.upd(lo,lo+f.c[sym],f.tot); f.bump(sym); return sym

def _fwd(data):
    toks=TOK.findall(data)
    n=len(toks); e=Enc()
    f=Fen(n+1); f.add(0,1)          # 0 = escape
    bm=Fen(256); [bm.add(i,1) for i in range(256)]
    lm=Fen(64); [lm.add(i,1) for i in range(64)]
    idx={}; 
    for t in toks:
        s=idx.get(t)
        if s is None:
            _code(e,f,0)
            s=len(idx)+1; idx[t]=s; f.add(s,1)
            L=len(t)
            while L>=63: _code(e,lm,63); L-=63
            _code(e,lm,L)
            for ch in t: _code(e,bm,ch)
        else: _code(e,f,s)
    return n.to_bytes(4,'big')+e.finish()

def _inv(blob):
    n=int.from_bytes(blob[:4],'big'); d=Dec(blob[4:])
    f=Fen(n+1); f.add(0,1)
    bm=Fen(256); [bm.add(i,1) for i in range(256)]
    lm=Fen(64); [lm.add(i,1) for i in range(64)]
    voc=[None]; out=[]
    for _ in range(n):
        s=_decode(d,f)
        if s==0:
            L=0
            while True:
                x=_decode(d,lm); L+=x
                if x<63: break
            t=bytes(_decode(d,bm) for _ in range(L))
            voc.append(t); f.add(len(voc)-1,1)
            out.append(t)
        else: out.append(voc[s])
    return b''.join(out)

_F=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
def _lz(b): return lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)
def _unlz(b): return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=_F)

def compress(data):
    c=[b'\0'+_lz(data)]
    if data: c.append(b'\1'+_fwd(data))
    return min(c,key=len)
def decompress(data):
    if not data: return b''
    return _unlz(data[1:]) if data[0]==0 else _inv(data[1:])
