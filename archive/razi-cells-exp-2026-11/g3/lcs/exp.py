import random, time

def make(a):
    masks = [0]*256
    bit = 1
    for ch in a:
        masks[ch] |= bit
        bit <<= 1
    return masks

def v_dict(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks={}
    bit=1
    for ch in a:
        masks[ch]=masks.get(ch,0)|bit
        bit<<=1
    full=(1<<m)-1
    V=full
    get=masks.get
    for ch in b:
        p=get(ch,0)
        if p:
            U=V&p
            V=(V+U)|(V-U)
    return m-(V&full).bit_count()

def v_list_branch(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks=make(a)
    full=(1<<m)-1
    V=full
    for ch in b:
        p=masks[ch]
        if p:
            U=V&p
            V=(V+U)|(V-U)
    return m-(V&full).bit_count()

def v_list_nobranch(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks=make(a)
    full=(1<<m)-1
    V=full
    for ch in b:
        p=masks[ch]
        U=V&p
        V=(V+U)|(V-U)
    return m-(V&full).bit_count()

def v_list_xor(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks=make(a)
    full=(1<<m)-1
    V=full
    for ch in b:
        p=masks[ch]
        U=V&p
        V=(V+U)|(V^U)
    return m-(V&full).bit_count()

def v_list_np(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks=make(a)
    full=(1<<m)-1
    nps=[full^x for x in masks]
    V=full
    for ch in b:
        U=V&masks[ch]
        V=(V+U)|(V&nps[ch])
    return m-(V&full).bit_count()

def v_unroll4(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks=make(a)
    n=len(b)
    full=(1<<m)-1
    V=full
    i=0
    n4=n-(n&3)
    while i<n4:
        p=masks[b[i]]; U=V&p; V=(V+U)|(V-U)
        p=masks[b[i+1]]; U=V&p; V=(V+U)|(V-U)
        p=masks[b[i+2]]; U=V&p; V=(V+U)|(V-U)
        p=masks[b[i+3]]; U=V&p; V=(V+U)|(V-U)
        i+=4
    while i<n:
        p=masks[b[i]]; U=V&p; V=(V+U)|(V-U)
        i+=1
    return m-(V&full).bit_count()

def v_unroll4b(a,b):
    if len(a)>len(b): a,b=b,a
    m=len(a)
    if m==0: return 0
    masks=make(a)
    n=len(b)
    full=(1<<m)-1
    V=full
    i=0
    n4=n-(n&3)
    while i<n4:
        U=V&masks[b[i]]; V=(V+U)|(V-U)
        U=V&masks[b[i+1]]; V=(V+U)|(V-U)
        U=V&masks[b[i+2]]; V=(V+U)|(V-U)
        U=V&masks[b[i+3]]; V=(V+U)|(V-U)
        i+=4
    while i<n:
        U=V&masks[b[i]]; V=(V+U)|(V-U)
        i+=1
    return m-(V&full).bit_count()

random.seed(7)
cases=[
 (bytes(random.randrange(97,101) for _ in range(3000)), bytes(random.randrange(97,101) for _ in range(3000))),
 (bytes(random.randrange(97,123) for _ in range(3000)), bytes(random.randrange(97,123) for _ in range(3000))),
 (bytes(random.randrange(97,99) for _ in range(3000)), bytes(random.randrange(97,99) for _ in range(3000))),
]
impls=[v_dict,v_list_branch,v_list_nobranch,v_list_xor,v_list_np,v_unroll4,v_unroll4b]
ref=[v_dict(a,b) for a,b in cases]
for f in impls:
    got=[f(a,b) for a,b in cases]
    assert got==ref,(f.__name__,got,ref)
    best=1e9
    for _ in range(3):
        t=time.perf_counter()
        reps=0
        while time.perf_counter()-t<0.35:
            for a,b in cases: f(a,b)
            reps+=1
        dt=time.perf_counter()-t
        best=min(best,reps*3/dt)
    print(f"{f.__name__:20s} {best:8.1f} cases/s")
