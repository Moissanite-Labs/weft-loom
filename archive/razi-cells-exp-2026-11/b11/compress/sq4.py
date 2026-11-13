import lzma, re
TOK = re.compile(rb' ?[A-Za-z]{1,60}|[0-9]|[^A-Za-z0-9]{1,60}')
HALF=1<<31; Q=1<<30; Q3=3<<30; MASK=(1<<32)-1
LIM=1<<15; INC=1

class Fen:
    __slots__=('n','t','c','tot')
    def __init__(s,n,init=0):
        s.n=n; s.t=[0]*(n+1); s.c=[0]*n; s.tot=0
        if init:
            for i in range(n): s.add(i,init)
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

class Enc:
    def __init__(s): s.low=0; s.high=MASK; s.pend=0; s.bits=[]
    def _bit(s,b):
        s.bits.append(b)
        if s.pend: s.bits.extend([1-b]*s.pend); s.pend=0
    def enc(s,lo,hi,tot):
        r=s.high-s.low+1
        s.high=s.low+(r*hi)//tot-1
        s.low=s.low+(r*lo)//tot
        while True:
            if s.high<HALF: s._bit(0)
            elif s.low>=HALF: s._bit(1); s.low-=HALF; s.high-=HALF
            elif s.low>=Q and s.high<Q3: s.pend+=1; s.low-=Q; s.high-=Q
            else: break
            s.low<<=1; s.high=(s.high<<1)|1
    def finish(s):
        s.pend+=1
        s._bit(0 if s.low<Q else 1)
        bits=s.bits
        while len(bits)%8: bits.append(0)
        if not bits: return b''
        return int(''.join(map(str,bits)),2).to_bytes(len(bits)//8,'big')

class Dec:
    def __init__(s,data):
        s.bits=bin(int.from_bytes(data,'big'))[2:].zfill(len(data)*8) if data else ''
        s.pos=0; s.low=0; s.high=MASK; s.val=0
        for _ in range(32): s.val=(s.val<<1)|s._nb()
    def _nb(s):
        p=s.pos
        if p<len(s.bits):
            s.pos=p+1; return 1 if s.bits[p]=='1' else 0
        return 0
    def target(s,tot):
        return ((s.val-s.low+1)*tot-1)//(s.high-s.low+1)
    def update(s,lo,hi,tot):
        r=s.high-s.low+1
        s.high=s.low+(r*hi)//tot-1
        s.low=s.low+(r*lo)//tot
        while True:
            if s.high<HALF: pass
            elif s.low>=HALF: s.low-=HALF; s.high-=HALF; s.val-=HALF
            elif s.low>=Q and s.high<Q3: s.low-=Q; s.high-=Q; s.val-=Q
            else: break
            s.low<<=1; s.high=(s.high<<1)|1; s.val=(s.val<<1)|s._nb()

def _fwd(data):
    toks=TOK.findall(data)
    E=Enc(); f0=Fen(LIM); f0.add(0,1); bm=Fen(256,1); lm=Fen(62,1)
    voc=[None]; vid={}; ctxs={}; p=0
    for tok in toks:
        sym=vid.get(tok)
        c=ctxs.get(p)
        if c is None: c=ctxs[p]=[{},0]
        d,total=c; tot=total+len(d)
        if tot:
            if sym is not None and sym in d:
                lo=0
                for k,v in d.items():
                    if k==sym: break
                    lo+=v
                E.enc(lo,lo+v,tot)
                d[sym]=v+INC; c[1]=total+INC; p=sym; continue
            E.enc(total,tot,tot)
        if sym is not None:
            lo=f0.prefix(sym); E.enc(lo,lo+f0.c[sym],f0.tot)
        else:
            E.enc(0,f0.c[0],f0.tot)
            L=len(tok); lo=lm.prefix(L); E.enc(lo,lo+lm.c[L],lm.tot); lm.add(L,1)
            for b in tok:
                lo=bm.prefix(b); E.enc(lo,lo+bm.c[b],bm.tot); bm.add(b,1)
            sym=len(voc)
            if sym>=LIM: raise ValueError
            voc.append(tok); vid[tok]=sym
        f0.add(sym,1); d[sym]=INC; c[1]=total+INC; p=sym
    return len(toks).to_bytes(4,'big')+E.finish()

def _inv(blob):
    n=int.from_bytes(blob[:4],'big'); D=Dec(blob[4:])
    f0=Fen(LIM); f0.add(0,1); bm=Fen(256,1); lm=Fen(62,1)
    voc=[None]; ctxs={}; p=0; out=[]
    for _ in range(n):
        c=ctxs.get(p)
        if c is None: c=ctxs[p]=[{},0]
        d,total=c; tot=total+len(d)
        if tot:
            t=D.target(tot)
            if t<total:
                lo=0
                for k,v in d.items():
                    if lo+v>t: break
                    lo+=v
                D.update(lo,lo+v,tot); d[k]=v+INC; c[1]=total+INC; p=k; out.append(voc[k]); continue
            D.update(total,tot,tot)
        t=D.target(f0.tot); sym=f0.find(t); lo=f0.prefix(sym); D.update(lo,lo+f0.c[sym],f0.tot)
        if sym==0:
            t=D.target(lm.tot); L=lm.find(t); lo=lm.prefix(L); D.update(lo,lo+lm.c[L],lm.tot); lm.add(L,1)
            bs=bytearray()
            for _ in range(L):
                t=D.target(bm.tot); b=bm.find(t); lo=bm.prefix(b); D.update(lo,lo+bm.c[b],bm.tot); bm.add(b,1); bs.append(b)
            sym=len(voc); voc.append(bytes(bs))
        f0.add(sym,1); d[sym]=INC; c[1]=total+INC; p=sym; out.append(voc[sym])
    return b''.join(out)

_F=[{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
def _lz(b): return lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F)
def _unlz(b): return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=_F)

def compress(data):
    c=[b'\0'+_lz(data)]
    if data:
        try: c.append(b'\1'+_fwd(data))
        except ValueError: pass
    return min(c,key=len)
def decompress(data):
    if not data: return b''
    return _unlz(data[1:]) if data[0]==0 else _inv(data[1:])
