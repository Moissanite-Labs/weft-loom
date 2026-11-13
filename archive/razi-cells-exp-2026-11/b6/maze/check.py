import collections, random, subprocess, sys

def reference(rows):
    h,w=len(rows),len(rows[0])
    start=next((r,c) for r in range(h) for c in range(w) if rows[r][c]==83)
    end=next((r,c) for r in range(h) for c in range(w) if rows[r][c]==69)
    queue=collections.deque([(start[0],start[1],0)])
    seen={start}
    while queue:
        r,c,d=queue.popleft()
        if (r,c)==end: return d
        for x,y in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0<=x<h and 0<=y<w and rows[x][y]!=35 and (x,y) not in seen:
                seen.add((x,y)); queue.append((x,y,d+1))
    return -1

def check():
    rng=random.Random(271828)
    cases=[b'SE\n',b'S#E\n',b'S\n.\nE\n',b'S..\n##.\nE..\n',b'S#\n#E\n']
    for _ in range(100):
        h,w=rng.randrange(2,30),rng.randrange(2,30)
        rows=[bytearray(46 if rng.random()>.35 else 35 for _ in range(w)) for _ in range(h)]
        a,b=rng.sample(range(w*h),2)
        rows[a//w][a%w]=83; rows[b//w][b%w]=69
        cases.append(b'\n'.join(rows)+b'\n')
    for data in cases:
        expected=reference(data.splitlines())
        result=subprocess.run([sys.executable,'maze.py'],input=data,stdout=subprocess.PIPE,check=True)
        assert result.stdout.strip()==str(expected).encode(), (data,expected,result.stdout)
    print('105 cases passed')
if __name__=='__main__': check()
