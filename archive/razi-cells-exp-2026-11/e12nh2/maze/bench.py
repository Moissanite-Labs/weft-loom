import random,time,maze
random.seed(7)
n=2000
rows=[bytearray(b'#' if random.random()<0.28 else b'.' for _ in range(n)) if 0 else ''.join('#' if random.random()<0.28 else '.' for _ in range(n)) for _ in range(n)]
rows[0]='S...'+rows[0][4:]
rows[1]='...'+rows[1][3:]
rows[-1]=rows[-1][:-4]+'...E'
rows[-2]=rows[-2][:-3]+'...'
t=time.time();r=maze.solve(rows);t=time.time()-t
small=maze.solve(["S.#","..#","#.E"])==4 and maze.solve(["S#E"])==-1
print(r,file=__import__('sys').stderr)
print(1/t if small and r>0 else 0)
