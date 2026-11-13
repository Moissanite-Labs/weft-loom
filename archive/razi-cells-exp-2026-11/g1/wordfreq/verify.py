import subprocess, sys, os, time

def run(inp):
    p = subprocess.run([sys.executable,'wf.py'], input=inp.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert p.returncode==0, p.stderr.decode()
    return p.stdout.decode()

cases=[
 ('',''),
 ('Hello hello WORLD world a A b B c','a 2\nb 2\nhello 2\nworld 2\nc 1\n'),
 ('the quick brown fox jumps over the lazy dog. The THE!','the 4\nbrown 1\ndog 1\nfox 1\njumps 1\nlazy 1\nover 1\nquick 1\n'),
 ('xxx y','xxx 1\ny 1\n'),
 ('!!! ??? ...',''),
 ('a a a b b c','a 3\nb 2\nc 1\n'),
]
for inp,exp in cases:
    got=run(inp)
    assert got==exp,(inp,repr(got),repr(exp))
print('correctness ok')

if not os.path.exists('big.txt') or os.path.getsize('big.txt')<20_000_000:
    subprocess.check_call([sys.executable,'sample.py','big.txt'])
data=open('big.txt','rb').read()
t=time.time()
p=subprocess.run([sys.executable,'wf.py'], input=data, stdout=subprocess.PIPE)
el=time.time()-t
assert p.returncode==0
lines=p.stdout.decode().strip().split('\n')
assert len(lines)==10, lines
for l in lines:
    w,n=l.rsplit(' ',1); assert n.isdigit()
print('size',len(data),'secs %.3f'%el,'->',1/el)
print(p.stdout.decode())
