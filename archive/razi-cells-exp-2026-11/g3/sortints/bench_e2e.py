import subprocess, sys, time
ref = open('ref_1m.bin','rb').read() if __import__('os').path.exists('ref_1m.bin') else None
D = open('test_1m.txt','rb').read()
if ref is None:
    vals = sorted(map(int, D.split()))
    ref = ('\n'.join(map(str, vals)) + '\n').encode()
    open('ref_1m.bin','wb').write(ref)

cands = {
'c1_join': "import sys\ndef main():\n import numpy as np\n d=sys.stdin.buffer.read()\n a=np.fromstring(d.decode(),dtype=np.int64,sep=' ')\n a.sort()\n sys.stdout.buffer.write(('\\n'.join(map(str,a.tolist()))+'\\n').encode())\nmain()\n",
'c2_tr': "import sys\ndef main():\n import numpy as np\n d=sys.stdin.buffer.read()\n a=np.fromstring(d.decode(),dtype=np.int64,sep=' ')\n a.sort()\n t={91:None,93:None,44:10}\n sys.stdout.buffer.write((str(a.tolist()).translate(t)+'\\n').encode())\nmain()\n",
'c3_tr2': "import sys\ndef main():\n import numpy as np\n d=sys.stdin.buffer.read()\n a=np.fromstring(d.decode(),dtype=np.int64,sep=' ')\n a.sort()\n r=str(a.tolist()).replace('[','',1)[:-1].encode()\n sys.stdout.buffer.write(r.translate(bytes.maketrans(b', ',b'\n\n')).replace(b'\\n\\n',b'\\n'))\nmain()\n",
}
for name, src in cands.items():
    open('cand.py','w').write(src)
    best=1e9; ok=None
    for _ in range(4):
        t=time.perf_counter()
        p=subprocess.run([sys.executable,'cand.py'],stdin=open('test_1m.txt','rb'),stdout=subprocess.PIPE)
        dt=time.perf_counter()-t
        ok = p.stdout==ref
        best=min(best,dt)
    print(f"{name:12s} {best*1000:8.1f} ms ok={ok} rate={1e6/best:.0f}/s")
